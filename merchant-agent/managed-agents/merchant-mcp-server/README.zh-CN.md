# merchant-mcp-server

一个托管商家智能体所调用的 MCP server：在 `MerchantBackend` 之上的商家工具，由 `merchant_agent.executor` 执行，每个连接一个执行器（也就是一份 provenance 记录）。每个工具都按 registry 的描述与输入 schema 列出，所以托管智能体看到的契约与另外两条路径相同。默认服务于 retail 示例的 mock merchant。

```
hosted agent  ──MCP (streamable HTTP)──►  merchant_mcp_server.py  ──►  MerchantBackend  ──►  your systems
```

| 工具 | 类型 |
|---|---|
| `get_business_snapshot` | 读；记录 `present_metrics` 所解析的值 |
| `query_metrics` | 读；同上 |
| `get_campaign_performance` | 读；记录 campaign 来源 |
| `search_listings` | 读；记录 listing 来源 |
| `get_listing` | 读；记录来源，以及一次编辑所需的完整记录读取 |
| `get_inventory_alerts` | 读 |
| `get_order_issues` | 读 |
| `get_pricing_context` | 读 |
| `get_pending_changes` | 读；记录变更来源 |
| `recall_memories` | 读 |
| `stage_listing_update` | 暂存写；来源 + 一次 `get_listing` 读取；护栏 |
| `stage_price_update` | 暂存写；来源；护栏 |
| `stage_inventory_action` | 暂存写；来源；护栏 |
| `stage_promotion` | 暂存写；来源；深度上限；护栏 |
| `stage_campaign` | 暂存写；点名 campaign 时需来源；护栏 |
| `discard_change` | 写；变更来源 |
| `save_memory` | 写；经过校验与过滤；`always_ask` |
| `apply_change` | 线上写；变更来源；复核护栏；`always_ask` |

护栏在 backend 暂存时（`ChangeLedger`、`merchant_agent.changes`）和 `check_apply_change`（`merchant_agent.gates`）中运行。Presentation 工具是 manifest 中的自定义工具，由门户执行，因此这里不提供服务且 `stage_shows_preview` 关闭；没有 `load_skill`，因为平台自身加载 skills；也没有 `run_analysis`。

## 运行

```bash
python merchant-agent/managed-agents/merchant-mcp-server/merchant_mcp_server.py   # 127.0.0.1:8201/mcp
```

环境变量：`MERCHANT_MCP_HOST`、`MERCHANT_MCP_PORT`、`MERCHANT_MCP_MERCHANT_ID`、`MERCHANT_MCP_OPERATOR`、`MERCHANT_MCP_SESSION_ID`、`MERCHANT_MCP_MEMORY_FILE`。除非通过 `MERCHANT_MCP_UNSAFE_ALLOW_NO_AUTH=1` 声明你的认证网关已位于其前方，否则服务器拒绝除 loopback 以外的任何 host（`commerce_common.mcp_server`）；开发期间，通过一条终止于 loopback、并将 `Host` 头改写为 `127.0.0.1:<port>` 的 HTTPS 隧道访问它（否则服务器的 DNS 重绑定检查会返回 421）。

## 你的后端

```python
from merchant_mcp_server import build_server

server = build_server(backend=MyMerchantBackend(), memory_store=MyMemoryStore())
server.run(transport="streamable-http")
```

`build_server` 还接受一个 `MerchantAgentConfig`（按原样使用；apply 会复核其护栏限制，所以要让它与 backend 暂存时所用的一致）和一个 `memory_write_filter`。`default_config` 设置 `require_host_approval=False`，因为这条路径上的审批就是平台对 `apply_change` 的 `always_ask` 提示；你传入的 config 会按原样使用，所以也要设置 `require_host_approval=False`，否则每次 apply 都会被挂起（server 启动时打印通知）。执行器强制执行的规则列于 [`docs/safety.md`](../../../docs/safety.md)。

## 身份

参考服务器为一家商店和一位操作者行事，分别由 `MERCHANT_MCP_MERCHANT_ID` 和 `MERCHANT_MCP_OPERATOR` 指定；操作者是账本在每项变更上盖的戳。生产服务器应从已鉴权的请求中推导出两者，据此为每个连接构造一个 `MerchantSessionContext`，并以该身份作为执行器、账本和记忆的键；两者绝不作为工具参数出现。将服务器置于 HTTPS 之后，并在 Managed Agents 的 vault 中注册凭据。

测试：`pytest merchant-agent/managed-agents/merchant-mcp-server/tests` 通过内存中的 MCP 会话连接，并演练上表中的所有工具。
