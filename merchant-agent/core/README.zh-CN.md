# merchant-agent/core（包名 `merchant_agent`）

商家智能体三条运行路径所共有的部分。回合主循环位于 `../runtime-messages-api/` 与 `../runtime-agent-sdk/`；托管路径的服务器位于 `../managed-agents/`。一个部署需要实现 `MerchantBackend` 并构造一个 `MerchantAgentConfig`；其余部分原样使用。[`docs/backends.md`](../../docs/backends.md) 介绍了带 variants 的 listing，以及当平台无法提供某个数字时该返回什么。

| 模块 | 职责 |
|---|---|
| `types.py` | Listing（一个商品族的 `options`、其 `variants`（含 `option_values` 与 `variant_of`））、快照与序列（商店无法提供的数字为带 `note` 的 `None`）、`DataLimitation`、告警、问题、定价上下文、活动、草稿、`StagedChange`、`MerchantSessionContext`、`MerchantSessionState` |
| `backend.py` | `MerchantBackend`：8 个读方法、5 个 `stage_*` 方法，以及 `get_pending_changes`、`apply_change`、`discard_change`；可选的 `execute_analysis_query`、`get_analysis_schema`、`get_merchant_context` |
| `config.py` | `MerchantAgentConfig`：分析设置与预算、`enable_*` 系统开关、护栏限制、审批、`stage_shows_preview`、grounding 词表 |
| `prompt.py` | `build_static_system`（带缓存）与 `build_dynamic_context`（带 fence，按请求生成） |
| `tools/registry.py` | 工具契约，按固定顺序；设置 `enable_analysis` 时加入 `run_analysis` |
| `tools/presentation.py` | 三个内置 presentation 工具的 payload 结构（chips 在 `commerce_common` 中） |
| `enrichment.py` | 指标选择解析为会话值、digest 条目关联到记录、从暂存记录构建预览；流式输出时的部分 payload |
| `changes.py` | `check_guardrails`（暂存时和应用时各运行一次）与内存 `ChangeLedger` |
| `gates.py` | listing 与 campaign 来源、options hold（商品族 listing 按 variant 定价和补货）、apply 与 discard 门控、跟进提醒文案 |
| `grounding.py` | 指标与队列（queue）grounding 规则，以及 `change_requested` 检测器 |
| `serialization.py` | 工具结果 payload：搜索头、带 variant 行的 listing 记录、定价上下文、告警 |
| `analysis.py` | `run_analysis` 契约：委托的提示词与工具、`check_analysis_sql`、`cap_analysis_table`、从 `AnalysisResult` 派生的指标 payload |
| `fencing.py`、`memory.py` | `merchant_data` 围栏与抽取提示词 |
| `executor.py` | `MerchantToolExecutor`：在共享框架之上每个工具一个 handler；被继承后作为 `executor_class` 传入；`build_memory` |

测试：`pytest merchant-agent/core/tests`。
