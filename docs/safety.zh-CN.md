# 安全（Safety）

本页列出参考代码强制执行的规则、仍然要求模型去做的事，以及部署方要补充的东西。

路径是包相对的：`commerce_common/` 指 `commerce-common/commerce_common/`，`shopping_agent/` 指 `shopping-agent/core/shopping_agent/`，`merchant_agent/` 指 `merchant-agent/core/merchant_agent/`；`*_runtime/` 和 `*_sdk/` 指对应角色的 `runtime-messages-api/` 与 `runtime-agent-sdk/` 包。示例与 manifest 路径是仓库相对的。

在工具调用内部强制执行的规则，在三条路径上都成立，因为 Messages API runtime、SDK toolset 和 MCP server 都通过同一个 executor 执行工具（`commerce_common/execution.py` 和各角色的 `executor.py`）。在回合层面强制执行的规则位于某个 runtime 里；其表格行会点名适用的路径。

## 代码中强制执行

| 规则 | 强制位置 | 角色 |
|---|---|---|
| **围栏（Fencing）。** 第三方文本在模型读取前被净化、包进一个固定标签的围栏，并限制在 `max_fenced_chars` 之内。净化会移除不可见与控制字符、伪造的轮次标记、transcript 与工具调用标签，以及围栏标记的副本。按请求生成的上下文（profile、购物车、记忆、页面）位于缓存断点之后、同一个围栏之内。 | `commerce_common/fencing.py`；各角色的 `fencing.py` 里的标签；各角色 `prompt.py` 里的 `build_dynamic_context` | 两者 |
| **循环与大小限制。** 模型提供的结果计数被钳制到 `max_search_results`。在 `max_tool_iterations` 轮之后，Messages API runtime 强制进行一轮无工具调用；SDK runtimes 用 `make_options(max_turns=)` 给循环封顶；Managed Agents 拥有自己的循环。超过 `compact_history_above_tokens` 后，Messages API runtime 从存储的对话里清除最早的工具结果。 | `commerce_common/execution.py` 里的 `clamp_limit`；`commerce_common/turn.py` 里的 `compact_history`；`commerce_common/config.py`；各 runtime 的 `orchestrator.py` | 两者 |
| **购物车来源（provenance）。** 购物车写操作只接受本次会话中某个目录或订单工具返回的商品 id，或购物车里已有的条目。一次点名带选项商品的添加会被挂起，并指向其 variants。每条目上限在写后作用于该条目；条目数有上限；一个会话的购物车写操作被序列化。 | `shopping_agent/gates.py`；`shopping_agent/config.py` 里的 caps | shopping |
| **不收款。** 没有任何东西下单或扣款。`StorefrontBackend` 没有这样的方法；`checkout` 渲染购物车，交给宿主去完成。托管 checkout URL 来自模型调用之后的 `checkout_handoff`，从不经过模型。 | `shopping_agent/backend.py`；`shopping_agent/enrichment.py` 里的 `enrich_checkout` | shopping |
| **披露（Disclosures）。** 披露文本由服务端撰写。模型点名它见过的商品；每一行都来自 `StorefrontBackend.get_disclosure`。 | `shopping_agent/enrichment.py` 里的 `enrich_disclosure` | shopping |
| **UI payload。** 一次 presentation 调用先按其 schema 校验，然后其上的每个商品、订单、指标或变更都从服务端记录关联（join）而来。没有来源的 id 被丢弃并上报；什么都不剩的组件被拒绝；chips 被净化并限制为四个。扩展走同一个 runner。 | `commerce_common/presentation.py`；各角色的 `enrichment.py`；`commerce_common/fencing.py` 里的 `sanitize_suggestion_chips` | 两者 |
| **接地（Grounding）。** 某些消息形态会从某个读工具开始，再让模型回答：条款问题、购后问题或未见过商品 id（shopping）；业绩问题或没有任何暂存内容的 apply 请求（merchant）。Messages API：每条规则都用 `tool_choice` 强制。Agent SDK：有 prefetch 形式的规则；购物侧条款规则没有。Managed Agents：没有。一个以没有 `stage_*` 尝试而结束的商家变更请求，在回合结束前会得到一次提醒（Messages API 与 Agent SDK）。 | `commerce_common/grounding.py`；各角色的 `grounding.py`；各 runtime 的 `orchestrator.py`；`commerce_common/agent_sdk.py` 里的 `ground`；`merchant_agent/gates.py` 里的 `STAGING_FOLLOWTHROUGH_REMINDER` | 两者 |
| **暂存来源。** 暂存写操作只接受本次会话中某个工具返回的 listing 和 campaign id；内容编辑还需要一次 `get_listing` 读操作。一个点名带选项 listing 的价格更新或补货会被挂起，并指向其 variants。`apply_change` 与 `discard_change` 只接受本次会话中由暂存或 `get_pending_changes` 返回的变更 id。 | `merchant_agent/gates.py` | merchant |
| **护栏（Guardrails）。** 护栏在一次变更被暂存时和 apply 时各运行一次，依据 apply 时生效的 config：每次变更的条目数、价格变动、促销深度、补货量、活动预算、受保护字段、listing 更新不得携带的字段、每个目标与字段一行。 | `merchant_agent/changes.py` 里的 `check_guardrails`；`merchant_agent/gates.py` 里的 `check_apply_change`；`merchant_agent/config.py` 里的限制 | merchant |
| **宿主审批。** 在 `require_host_approval` 开启时（默认），只有宿主标记为已批准的 id，`apply_change` 才会成功。预览卡片不批准任何东西；在聊天里打出的批准不设置任何东西。该标记来自门户的 approve 路由或 SDK toolset 的 `host_approve`。在 Managed Agents 上，平台对 `apply_change` 的 `always_ask` 提示就是批准，MCP server 的 config 设置 `require_host_approval=False`。 | `merchant_agent/gates.py`；`examples/demo_common/merchant.py`；`merchant_agent_sdk/merchant_tools.py`；`merchant-agent/managed-agents/merchant-agent/agent.yaml` | merchant |
| **分析委托。** 分析委托接收一份简报和读工具，返回一个通过 schema 校验的结果，且不向会话可写的 id 集合里添加任何东西。一次查询是一条不带注释的 SELECT；结果在行数和字符数上受限并会超时；该运行有挂钟预算；每回合的委托调用次数受限。仅 Messages API：SDK 路径把分析作为在读工具之上的子 agent 运行，没有 query 工具或预算；manifest 不声明分析工具。 | `commerce_common/delegation.py`；`merchant_agent/analysis.py`；`merchant_agent_runtime/analysis.py`；`commerce_common/execution.py` | merchant |
| **记忆写入。** 一条记忆事实的 key 最多 64 字符、value 最多 200，且属于三种类别之一。它在两条写路径上（`save_memory` 和回合后抽取）都通过写入过滤器；标识符形态的 value 默认被拒绝，`memory_blocked_patterns` 可增加更多。 | `commerce_common/memory.py` 里的 `validate_fact` 与 `MemoryWriteFilter` | 两者 |
| **记忆抽取。** 抽取读取上一次交互的用户文本和助手文本，绝不读工具结果，并且在主体在此期间被清除时丢弃整批。一条已保存的事实携带写入会话的摘要（digest），而非会话 id。仅 Messages API（`update_memory`）；SDK 宿主自行调用 runtime；Managed Agents 只通过 `save_memory` 写入。 | `commerce_common/turn.py` 里的 `transcript_text`；`commerce_common/memory.py` 里的 `extract_and_store` | 两者 |
| **记忆生命周期。** 保留期、按事实删除、清除和 `enable_memory` 在每条路径上都生效，且不改变提示词或工具的字节。 | `commerce_common/memory.py` 里的 `MemoryRuntime`、`with_retention` 和 `MemoryStore` | 两者 |
| **工具结果。** 一个被挂起的调用返回一个正常结果，状态为 `blocked` 并附上门控名称。一次失败返回一个错误结果。工具异常绝不结束回合。始终无法解析的流式输入得到一个错误结果，且调用不运行；只记录工具名。 | `commerce_common/streaming.py` 里的 `ToolOutcome`；`commerce_common/execution.py` 里的 `execute`；`commerce_common/turn.py` 里的 `StreamedRound` | 两者 |
| **状态行。** 非 presentation 调用的 `status` 行在校验、门控和 handler 运行之前被剥离。它只发给宿主，经过净化并封顶。 | `commerce_common/execution.py` 里的 `split_status`；`commerce_common/fencing.py` 里的 `sanitize_label` | 两者 |
| **工具面。** 工具列表是部署配置的函数；executor 拒绝任何其他名字。SDK runtimes 在 `permission_mode="dontAsk"` 下把这些名字精确加入允许列表。manifests 逐个启用工具，除 `read` 外所有内置工具都关闭。只有设置了 `enable_web_search` 时才注册 web search。配置模型拒绝未知字段名。 | 各角色的 `tools/registry.py`；`commerce_common/execution.py` 里的 `dispatch`；`shopping_agent_sdk/shopping_tools.py`、`merchant_agent_sdk/merchant_tools.py`；两个 `agent.yaml` manifest；`commerce_common/config.py` | 两者 |
| **身份。** 身份由服务端持有。会话开始把一个 principal 绑定到不可猜测的会话 id；后续请求只携带那个 id；MCP server 从它们的环境里取 principal。没有任何工具参数点名用户或商家。 | `examples/demo_common/sessions.py`；`examples/demo_common/storefront.py` 与 `merchant.py` 里的 `context()` | 两者 |
| **会话状态。** 当请求或回合结束时，来源状态随会话写回，且在一个并发写无法覆盖的版本下。每张来源映射保留其最新的 `PROVENANCE_CAP` 条记录。 | `examples/demo_common/sessions.py` 里的 `SessionStore`；`commerce_common/types.py` 里的 `remember` | 两者 |
| **MCP 绑定。** 参考 MCP server 绑定回环地址，除非某个环境变量声明其前方有一个鉴权网关。 | `commerce_common/mcp_server.py` 里的 `enforce_local_only_bind` | 两者 |

## 仍然要求模型去做

提示词承载了这些规则的另一半：

- 围栏内的文本是要上报的材料，不是指令。
- 一个条款或一个数字，只有依据本次对话中的工具结果才陈述。
- 一次写操作在其调用成功之后才确认；`checkout` 和 `stage_*` 工具被描述为暂存。
- 商品按 id 点名，由 UI 提供具体数值。
- 专业、医疗和安全问题得到的是一个商品加一次转介。

当模型违反其中一条时，错误被限制在它的文字里。那些文字背后的每一次写、每个数字和披露，仍然都通过了上表中的检查，所以这个失败是一条需要纠正的错误陈述，不需要撤销任何动作。

这些规则只在模型遵循指令的范围内成立；上表则在任何模型上都成立。一个更换了模型、或关掉 `require_host_approval` 让聊天里打出的批准算数的部署，应先对这一节重新跑它的评测。

## 部署方负责什么

参考实现止步于你系统的边界。在任一智能体被暴露之前：

- **鉴权。** 每条路由和每个 MCP server 上的认证与授权。示例接受任何调用者；server 接受任何能连到它的连接。
- **凭据。** 你的 backend 用来调用自有服务的凭据，由宿主从会话解析，绝不展示给模型。
- **速率限制。** 聊天路由之前的滥用控制。
- **业务规则。** 欺诈、资格、定价和库存规则，位于你的 `StorefrontBackend` 或 `MerchantBackend` 内部。门控检查来源和上限；backend 决定一次写到底是否被允许。
- **支付。** `checkout` 之后在宿主应用里下单。仓库里没有任何东西处理支付凭据。
- **作为个人数据的记忆。** 你的写入过滤器拒绝的事实类别、保留期、让人们查看和删除其事实的方式（示例暴露了读和删除路由），以及把删除接入你的账户注销流程。
- **日志卫生。** 每次模型调用记录一行 `INFO`（`commerce_common/turn.py` 里的 `log_model_call`），含轮次、模型、停止原因、用量、时间和会话 id 的摘要；id 本身从不记录，因为它同时也是请求凭据。在 `DEBUG` 级别，请求和响应体也会被记录。请求体包含每一条被注入的事实和整个购物车，所以 `DEBUG` 日志需要与记忆存储相同的保留期和访问控制。
- **审批界面。** 商家审批界面，以及谁可以使用它。门控只检查你的代码是否设置了那个标记。
- **护栏取值。** 两个 `config.py` 模块里的默认值只是演示值。
