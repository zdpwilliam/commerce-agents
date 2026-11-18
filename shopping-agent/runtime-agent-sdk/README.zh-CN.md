# shopping-agent/runtime-agent-sdk（包名 `shopping_agent_sdk`）

基于 [Claude Agent SDK](https://pypi.org/project/claude-agent-sdk/) 的购物智能体。SDK 负责运行主循环、缓存与技能加载；本包提供与 `../runtime-messages-api/` 相同的静态提示词、skills、工具契约和执行器，外加一个控制台（console）。当你的宿主消费一个已完成的回合、并且你要在 SDK 的主循环之上构建时，选择本包。

```
                 Claude Code CLI，由 SDK 启动
                 loop · caching · Skill 工具读取 .claude/skills/<flow>/SKILL.md
                            │  mcp__storefront__* 调用
                            ▼
   your process   shopping_tools.py: 基于 ShoppingToolExecutor 的进程内 MCP 服务器
                  agent.py: make_options() 构造选项；run_turn() 执行 grounding 并收集
                  StorefrontBackend: 默认 MockRetail；生产环境用你自己的
```

## 配置

`scripts/install.sh` 安装本包及其依赖；`claude-agent-sdk` 打包了它启动的 CLI。凭据：`ANTHROPIC_API_KEY`，或一个已认证的 Claude Code 安装。其他平台：见 `docs/deployment.md`。

## 运行

```bash
python shopping-agent/runtime-agent-sdk/main.py                       # 与 mock 商店对话
python shopping-agent/runtime-agent-sdk/main.py --once "a light tent for two under $250"
```

控制台会打印回复、每个 presentation payload（JSON 形式）、被调用的工具以及花费。在代码中：

```python
from claude_agent_sdk import ClaudeSDKClient
from shopping_agent_sdk import make_options, run_turn

options, toolset = make_options(backend=MyStorefrontBackend())   # backend 默认为 mock
async with ClaudeSDKClient(options=options) as client:
    result = await run_turn(client, "I need a tent for two people", toolset=toolset)
    result.text          # 回复
    result.ui            # [{"component": ..., "payload": ...}] 待渲染
    result.tool_calls    # 按调用顺序的工具名
```

`make_options` 还接受 `config`、`session_id`、`user_id`、`max_turns` 和 `skills_dir`（用以替换 `../skills` 的项目自有 skills 目录）。它返回的 toolset 持有该会话的 provenance 状态和一个内存中的 `MemoryStore`；一个带有持久化记忆的宿主可自行构造 `ShoppingToolset(memory_store=...)`，并以 `agent.py` 的方式构造选项。

## 复用了什么

- **Skills**：`ensure_project_skills` 将 `../skills/*` 链接到本目录中、被 gitignore 的 `.claude/skills/`，并且选项允许这些名字使用 `Skill` 工具。`shopping_agent.prompt` 的静态提示词带有相同的索引，外加 `SKILL_TOOL_ADAPTER`（`commerce_common/agent_sdk.py`），它让模型指向 `Skill` 而非 `load_skill`。
- **Tools**：`shopping_tools.py` 注册 `shopping_agent.tools.registry` 中的每一个契约（除 `load_skill` 外，含描述与 schema），并通过 `ShoppingToolExecutor` 执行每个调用。选项以 `permission_mode="dontAsk"` 将那些名字加入允许列表，并且除 `Skill` 外不挂载任何内置工具。
- **Backend**：任意 `StorefrontBackend`，传入 `make_options`。

## 与 Messages API runtime 的差异

- **UI 在回合结束后才到达。** Presentation payload 在 toolset 上收集，并通过 `result.ui` 返回；没有部分卡片（partial-card）流。
- **回合收尾是一个 hook。** 一个工具批次后的 hook 会在收尾组件上结束回合；在较旧的 CLI 上，则由模型写一句收尾文字替代。
- **Grounding 在宿主侧。** `run_turn` 运行订单与目录 grounding 规则所需的读操作，并将结果追加到消息中；terms（条款）规则仍是一条提示词规则。
- **没有 Session context 块。** Profile、已保存的记忆和购物车通过 `get_preferences` 的结果传入，并且有两个工具描述被相应改写以说明这一点。
- **此处未应用。** 记忆抽取（调用 `toolset.memory`）、`thinking_effort`（设置 `options.effort`）和 `enable_web_search`（添加 CLI 的 web 工具）。
- **没有游离上下文。** `make_options` 阻止 CLI 加载工作目录之上的任何 `CLAUDE.md`。
- **平台选择。** CLI 的环境；见 [`docs/deployment.md`](../../docs/deployment.md)。

## 测试

`pytest shopping-agent/runtime-agent-sdk/tests` 在进程内调用已注册的工具，无需凭据；该测试套件还会将已注册的工具面与 `shopping_agent.tools.registry` 比对，因此本包不会落后于 core。
