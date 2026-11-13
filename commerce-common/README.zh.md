# commerce-common（包名 `commerce_common`）

这是两种 agent 角色共同依赖的机制基础。角色包（`shopping_agent`、
`merchant_agent`）在其之上叠加各自的类型、提示词、工具契约与把关逻辑；
运行时则同时导入这两部分。每种机制对应一个模块：

| 模块 | 内容 |
|---|---|
| `config.py` | `BaseAgentConfig`：身份、模型、预算、能力、记忆、上限（caps） |
| `fencing.py` | `Fence`：对模型当作数据读取的文本进行清洗与隔离；片段（chip）卫生处理 |
| `memory.py` | `MemoryStore` 契约、写入过滤器、`validate_fact`、抽取、`MemoryRuntime` |
| `skills.py` | `SkillRegistry`：加载 `SKILL.md` 目录并渲染提示词索引 |
| `prompt_assembly.py` | 缓存断点所在之处（静态系统块、工具数组、最新的持久化消息），以及按请求上下文块及其时钟所在之处 |
| `grounding.py` | `GroundingRule` 与匹配器；`first_forced_tool` |
| `presentation.py` | `PresentationComponent`、`PresentationExtension`、`run_presentation`；用于 `ui_partial` 帧的 `enrich_partial` |
| `delegation.py` | `DelegateExtension`：工具背后一个隔离的模型任务 |
| `execution.py` | `BaseToolExecutor`：调度、失败阶梯、技能、呈现、委派、记忆；`split_status`（一次调用的 `status` 行，交给宿主）|
| `streaming.py` | `AgentEvent`（事件列表见模块文档字符串）、`ToolOutcome`、`to_sse` |
| `turn.py` | Messages API 的轮次辅助：用户文本、历史压缩、即时工具调度、`StreamedRound`（一轮在流式输出时的 `ui_partial` 帧；针对无法解析输入的报错结果）、`round_closes_turn`（一轮已渲染的呈现调用，其中包含片段，用于结束本轮）、工具结果块、用量、模型调用日志记录、转录切片 |
| `agent_sdk.py` | SDK 运行时的共享管线及其 `round_closes_turn` 钩子（需要 `claude-agent-sdk`）|
| `mcp_server.py` | MCP 服务器的共享管线：`registrar`（剔除被关闭的工具与 `status` 参数）以及回环绑定守卫（需要 `mcp`）|
| `manifest.py` | 解析一个 Managed Agents 清单；由 `scripts/deploy_managed_agent.sh` 调用 |
| `testing.py` | 用于流式与 `create` 客户端调用的脚本化替身，外加一个 spy 记忆存储，用于无需凭证的测试 |
| `types.py` | `MemoryFact`、`MemoryCategory`、`ClockContext` |

附加项：`[sdk]` 与 `[mcp]` 用于安装 `agent_sdk.py` 和
`mcp_server.py` 的可选依赖；`[examples]` 补充示例宿主所需的导入，
`requirements-dev.txt` 固定测试工具版本。

测试：`pytest commerce-common/tests`。
