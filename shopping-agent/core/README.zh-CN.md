# shopping-agent/core（包名 `shopping_agent`）

购物智能体三条运行路径（runtime paths）所共有的部分。回合（turn）主循环位于 `../runtime-messages-api/` 与 `../runtime-agent-sdk/`；托管（hosted）路径的服务器位于 `../managed-agents/`。一个部署需要实现 `StorefrontBackend` 并构造一个 `ShoppingAgentConfig`；其余部分原样使用。[`docs/backends.md`](../../docs/backends.md) 介绍了如何将带有选项（options）和变体（variants）的目录映射到 `Product`。

| 模块 | 职责 |
|---|---|
| `types.py` | 商品（一个商品族的 `options`、其 `variants`（含 `option_values` 与 `variant_of`））、购物车、订单、政策、披露信息、`ShoppingSessionContext`、`ShoppingSessionState` |
| `backend.py` | `StorefrontBackend`：11 个必需方法，外加 `get_account_context`、`get_disclosure` 和 `checkout_handoff`；`NotOffered`（某件商品或卖家不提供服务）与 `Unavailable`（在目录中但缺货） |
| `config.py` | `ShoppingAgentConfig`：能力开关、`enable_*` 系统开关、购物车上限、grounding 词表 |
| `prompt.py` | `build_static_system`（带缓存）与 `build_dynamic_context`（带 fence，按请求生成） |
| `tools/registry.py` | 工具契约，按固定顺序排列 |
| `tools/presentation.py` | 内置 presentation 工具的 payload 结构 |
| `enrichment.py` | 内置组件与会话记录的关联逻辑；流式输出时的部分 payload |
| `gates.py` | 购物车来源追踪（provenance）、options hold（一个商品族以其中一个 variant 加入）、数量上限、每会话写锁 |
| `grounding.py` | 政策、订单与目录的 grounding 规则 |
| `serialization.py` | 读操作工具返回的 payload |
| `fencing.py`、`memory.py` | `storefront_data` 的 fence 与抽取提示词 |
| `executor.py` | `ShoppingToolExecutor`：在共享框架之上每个工具一个 handler；被继承后作为 `executor_class` 传入 |

测试：`pytest shopping-agent/core/tests`。
