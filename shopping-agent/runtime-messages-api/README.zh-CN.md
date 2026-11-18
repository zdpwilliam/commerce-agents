# shopping-agent/runtime-messages-api（包名 `shopping_agent_runtime`）

购物智能体基于 Messages API 的回合主循环。`ShoppingAgent` 一次性构造静态提示词和工具数组，并在每个回合预取 profile、购物车和记忆事实，流式调用模型，通过 `shopping_agent.executor` 并发执行工具调用，并产生供宿主渲染的事件。四个示例 API 是围绕它的宿主应用（`examples/demo_common/storefront.py`）。

| 模块 | 职责 |
|---|---|
| `orchestrator.py` | `ShoppingAgent`：构造函数、`stream_turn`、`update_memory` |

## 使用

```python
from pathlib import Path

from commerce_common.streaming import to_sse
from shopping_agent import ShoppingAgentConfig, ShoppingSessionContext, ShoppingSessionState
from shopping_agent_runtime import ShoppingAgent

agent = ShoppingAgent(
    backend=your_backend,                       # 你的 StorefrontBackend
    skills_dir=Path("shopping-agent/skills"),
    config=ShoppingAgentConfig(brand_name="Your Store"),
    memory_store=your_store,                    # 可选；一个 commerce_common.memory.MemoryStore
    client=your_client,                         # 可选；见 docs/deployment.md
)

state = ShoppingSessionState()                # 按会话保存：provenance 与购物车状态
session = ShoppingSessionContext(session_id=sid, user_id=uid)
async for event in agent.stream_turn(messages, session, state):
    send(to_sse(event))
await agent.update_memory(messages, session)  # 回复之后；抽取运行于 memory_model
```

`messages` 是迄今的对话，以用户的消息结尾；回合会就地追加其助手消息和工具结果，因此宿主按原样保存该列表。事件类型列于 `commerce_common/streaming.py`；`ui` 事件携带经过校验和关联的 payload，`ui_partial` 事件在该调用仍在流式输出时携带同一组件，`cart_update` 在写操作之后携带整个购物车。API 或流错误会传出 `stream_turn`；宿主捕获它并发出一个 `error` 事件（见 `examples/demo_common/host.py`）。

## 该 runtime 给执行器增加了什么

- 当 `shopping_agent.grounding` 中的某条规则触发时，首轮通过 `tool_choice` 被钉在那一读操作工具上；在 `max_tool_iterations` 轮之后，最后一轮在没有工具的情况下运行。
- 工具调用被急切分派（eager dispatch）：一个调用在其内容块闭合的瞬间即执行，而模型仍在写该轮的其余部分（`eager_tool_dispatch`）。每次模型调用都在最新的持久化消息上带一个缓存断点（`rolling_conversation_cache`，仅放在出站请求上），并以 `thinking_effort` 发送 thinking。`eager_partial_frames` 将 `ui_partial` 帧从结构性变化切换为每次可见变化；一个调用的 `status` 行作为 `tool_call` 事件的 `label` 发出。
- 在 `close_on_presentation` 开启时，一个被 `round_closes_turn`（`commerce_common/turn.py`）接受的回合会在该处结束，因此 `messages` 可以以工具结果结尾。
- `extra_presentation_tools` 将一个部署的 `PresentationExtension`s 追加到工具数组。
- `agent.memory` 是部署的 `MemoryRuntime`；一个带有自有记忆的宿主通过 `agent.memory.store` 路由读与删除。

门控本身（fencing、provenance、caps、记忆校验）位于 `shopping_agent` 与 `commerce_common`；[`docs/safety.md`](../../docs/safety.md) 列出了它们。

凭据：默认客户端从环境中读取 `ANTHROPIC_API_KEY`（或一个 token 与 base URL）。测试无需任何凭据：`pytest shopping-agent/runtime-messages-api/tests` 用 `commerce_common.testing.FakeClient` 模拟模型。
