# storefront-mcp-server

一个托管购物智能体所调用的 MCP 服务器：在 `StorefrontBackend` 之上的 storefront 工具，由 `shopping_agent.executor` 执行，每个连接一个执行器（也就是一份 provenance 记录）。每个工具都按 registry 的描述与输入 schema 列出，所以托管智能体看到的契约与另外两条路径相同。默认服务于 retail 示例的 mock storefront。

```
hosted agent  ──MCP (streamable HTTP)──►  storefront_mcp_server.py  ──►  StorefrontBackend  ──►  your systems
```

| 工具 | 类型 |
|---|---|
| `search_products` | 读；记录 provenance |
| `get_product_details` | 读；记录 provenance |
| `get_cart` | 读 |
| `add_to_cart` | 写；受 provenance 门控并施加上限 |
| `update_cart_item` | 写；受 provenance 或购物车成员关系约束；施加上限 |
| `remove_from_cart` | 写；受 provenance 或购物车成员关系约束 |
| `get_preferences` | 读；profile 加上注入的记忆事实 |
| `save_memory` | 写；经过校验与过滤 |
| `recall_memories` | 读 |
| `get_orders` | 读；订单条目计入 provenance |
| `get_order_status` | 读 |
| `search_policies` | 读 |
| `get_fulfillment_options` | 读 |

Presentation 工具是 manifest 中的自定义工具，由宿主应用执行，因此这里不提供服务；也没有 `load_skill`，因为平台自身加载 skills。

## 运行

```bash
python shopping-agent/managed-agents/storefront-mcp-server/storefront_mcp_server.py   # 127.0.0.1:8200/mcp
```

环境变量：`STOREFRONT_MCP_HOST`、`STOREFRONT_MCP_PORT`、`STOREFRONT_MCP_USER_ID`、`STOREFRONT_MCP_SESSION_ID`、`STOREFRONT_MCP_MEMORY_FILE`。除非通过 `STOREFRONT_MCP_UNSAFE_ALLOW_NO_AUTH=1` 声明你的认证网关已位于其前方，否则服务器拒绝除 loopback 以外的任何 host（`commerce_common.mcp_server`）；开发期间，通过一条终止于 loopback、并将 `Host` 头改写为 `127.0.0.1:<port>` 的 HTTPS 隧道访问它（否则服务器的 DNS 重绑定检查会返回 421）。

## 你的后端

```python
from storefront_mcp_server import build_server

server = build_server(backend=MyStorefrontBackend(), memory_store=MyMemoryStore())
server.run(transport="streamable-http")
```

`build_server` 还接受 `ShoppingAgentConfig`（上限、记忆设置）和一个 `memory_write_filter`。执行器强制执行的规则列于 [`docs/safety.md`](../../../docs/safety.md)。

## 身份（Identity）

参考服务器为 `STOREFRONT_MCP_USER_ID` 指定的单一客户行事。生产服务器应从已认证的请求中推导出客户身份，并据此为每个连接构造一个 `ShoppingSessionContext`，再以该身份作为执行器、购物车和记忆的键；user id 绝不作为工具参数出现。将服务器置于 HTTPS 之后，并在 Managed Agents 的 vault 中注册凭据：每个客户会话一个 vault 凭据，或者一个服务凭据加上由你的网关在每次请求时校验的、带签名的客户声明。

测试：`pytest shopping-agent/managed-agents/storefront-mcp-server/tests` 通过内存中的 MCP 会话连接，并演练上表中的所有工具。
