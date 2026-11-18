# merchant-agent/runtime-messages-api（包名 `merchant_agent_runtime`）

商家智能体基于 Messages API 的回合主循环。`MerchantAgent` 一次性构造静态提示词和工具数组，并在每个回合预取商家上下文和记忆事实，流式调用模型，通过 `merchant_agent.executor` 并发执行工具调用，并产生供门户渲染的事件。四个示例 API 是围绕它的宿主应用（`examples/demo_common/merchant.py`）。

| 模块 | 职责 |
|---|---|
| `orchestrator.py` | `MerchantAgent`：构造函数、`stream_turn`、`update_memory` |
| `analysis.py` | `build_analysis_delegate` 与 `AnalysisRunner`，即 `run_analysis` 背后的循环 |

## 使用

```python
from pathlib import Path

from commerce_common.streaming import to_sse
from merchant_agent import MerchantAgentConfig, MerchantSessionContext, MerchantSessionState
from merchant_agent_runtime import MerchantAgent

agent = MerchantAgent(
    backend=your_backend,                       # 你的 MerchantBackend
    skills_dir=Path("merchant-agent/skills"),
    config=MerchantAgentConfig(brand_name="Your Store"),
    memory_store=your_store,                    # 可选；一个 commerce_common.memory.MemoryStore
    client=your_client,                         # 可选；见 docs/deployment.md
)

state = MerchantSessionState()                # 按会话保存：provenance 与审批标记
session = MerchantSessionContext(session_id=sid, merchant_id=mid, operator=who)
async for event in agent.stream_turn(messages, session, state):
    send(to_sse(event))
await agent.update_memory(messages, session)  # 回复之后；抽取运行于 memory_model
```

`messages` 是迄今的对话，以操作者的消息结尾；回合会就地追加其助手消息、工具结果和任何提醒，因此宿主按原样保存该列表；`operator` 会盖在该会话暂存的变更上。事件类型列于 `commerce_common/streaming.py`；`ui` 事件携带经过校验和关联的 payload，`ui_partial` 事件在调用仍在流式输出时携带组件，`change_update` 在每次变更移动时携带其完整记录（一次成功的 `stage_*` 调用也会发送预览卡片），而 `progress` 在 `run_analysis` 运行时携带分析委托的状态行。API 或流错误会传出 `stream_turn`；宿主捕获它并发出一个 `error` 事件（见 `examples/demo_common/host.py`）。

## 该 runtime 给执行器增加了什么

- 当 `merchant_agent.grounding` 中的某条规则触发时，首轮通过 `tool_choice` 被钉在那一读操作工具上；在 `max_tool_iterations` 轮之后，最后一轮在没有工具的情况下运行。
- 工具调用被急切分派：一个调用在其内容块闭合的瞬间即执行，而模型仍在写该轮的其余部分（`eager_tool_dispatch`）。每次模型调用都在最新的持久化消息上带一个缓存断点（`rolling_conversation_cache`，仅放在出站请求上）；每次调用（含分析委托）以 `thinking_effort` 发送 thinking。`eager_partial_frames` 将 `ui_partial` 帧从结构性变化切换为每次可见变化；一个调用的 `status` 行作为 `tool_call` 事件的 `label` 发出。
- 一个本会以文字或 chips 结束、却没有 `stage_*` 调用的变更请求（`change_requested`），会追加一次 `STAGING_FOLLOWTHROUGH_REMINDER`（`merchant_agent.gates`），并多跑一轮。
- 在 `close_on_presentation` 开启时，一个被 `round_closes_turn`（`commerce_common/turn.py`）接受的回合会在该处结束，因此 `messages` 可以以工具结果结尾。
- 设置 `enable_analysis` 时，`analysis.py` 构建 `run_analysis` 委托；一次运行在 `analysis_timeout_s` 处停止，executor 每回合允许 `max_delegate_calls_per_turn` 次运行。
- `extra_presentation_tools` 和 `extra_delegates` 追加一个部署的扩展；`agent.memory` 是其 `MemoryRuntime`，带自有记忆的门户通过 `agent.memory.store` 路由读与删除。

审批标记是宿主代码写 `state.approved_change_ids`；那道门和其他门（fencing、provenance、guardrails、记忆校验）位于 `merchant_agent` 与 `commerce_common`，[`docs/safety.md`](../../docs/safety.md) 列出了它们。

凭据：默认客户端从环境中读取 `ANTHROPIC_API_KEY`（或一个 token 与 base URL）。测试无需任何凭据：`pytest merchant-agent/runtime-messages-api/tests` 用 `commerce_common.testing.FakeClient` 模拟模型。
