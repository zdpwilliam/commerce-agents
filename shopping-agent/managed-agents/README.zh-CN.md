# shopping-agent/managed-agents

购物智能体作为 Anthropic 托管的智能体，运行在 [Managed Agents API](https://platform.claude.com/docs/en/managed-agents/overview)（测试版）上。平台负责运行主循环并持有会话；技能（skills）、提示词（prompt）和工具契约（tool contracts）来自本仓库；你的商业数据保存在你自己托管的 MCP 服务器之后。智能体每次调用只能看到该服务器返回的内容，其他一概不可见。

```
your app  ──user.message──►  hosted agent (agent.yaml: model, system.md, skills)
          ◄──agent.message, agent.custom_tool_use──┘        │ MCP over HTTPS, credential from a vault
                                                            ▼
                                   your infrastructure: storefront-mcp-server -> StorefrontBackend
```

| 路径 | 内容 |
|---|---|
| `shopping-agent/agent.yaml` | 清单（manifest）：5 个 skills、13 个 storefront 工具、7 个 presentation 工具 |
| `shopping-agent/system.md` | 系统提示词，由 `shopping_agent.prompt.build_static_system` 生成；其头部列出了差异点 |
| [`storefront-mcp-server/`](storefront-mcp-server/) | 基于 `StorefrontBackend` 的参考 MCP 服务器；即你需要替换的部分 |
| `../../scripts/deploy_managed_agent.sh` | 解析清单（`commerce_common.manifest`）并上传；默认执行 dry run（空跑） |

## 快速开始

```bash
scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent     # 打印 /v1/agents 的请求体

python shopping-agent/managed-agents/storefront-mcp-server/storefront_mcp_server.py
# 在 127.0.0.1:8200/mcp 提供服务；通过 HTTPS 隧道或你的网关访问它（详见其 README）。

export ANTHROPIC_API_KEY=<API_KEY>
export STOREFRONT_MCP_URL=https://<YOUR_HOST>/mcp
scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent --live
```

实时部署会上传五个 skills、创建智能体并打印其 id。会话需要一个 environment 以及一个保存了 MCP 服务器凭据的 vault；平台按 URL 将 vault 条目与清单中的服务器匹配。

```bash
H=(-H "content-type: application/json" -H "x-api-key: $ANTHROPIC_API_KEY"
   -H "anthropic-version: 2023-06-01" -H "anthropic-beta: managed-agents-2026-04-01")
curl -sS https://api.anthropic.com/v1/environments "${H[@]}" -d '{"name": "commerce",
  "config": {"type": "cloud", "networking": {"type": "limited", "allow_mcp_servers": true,
             "allowed_hosts": ["<YOUR_HOST>"]}}}'
curl -sS https://api.anthropic.com/v1/sessions "${H[@]}" -d '{"agent": "<AGENT_ID>",
  "environment_id": "<ENVIRONMENT_ID>", "vault_ids": ["<VAULT_ID>"]}'
```

然后向会话发送 `user.message` 事件并读取其事件流。

## 你的应用需要处理什么

- `agent.message`：助手文本；将其作为聊天内容渲染。
- `agent.custom_tool_use`：一次 presentation 工具调用。对照 `shopping_agent/tools/presentation.py` 校验 payload，用你自己的系统按 id 补全标题、价格和订单数据（`shopping_agent/enrichment.py` 是参考的关联逻辑），渲染后回复一个 `user.custom_tool_result`。每一次调用（包括 `present_suggestions`）都需要回复，否则会话会一直等待；此处模型会在 chips 的结果之后补一句收尾文字。
- `session.status_idle` 且 `stop_reason: requires_action`：一次写操作正在等待确认；展示你的 UI 并回复一个 `user.tool_confirmation`。

`shopping_agent/grounding.py` 中的 grounding 规则不会在这条路径上运行，因为工具选择由平台负责；相关轮次由提示词规则覆盖。

## 工具权限

MCP 工具集默认拒绝（deny-by-default）：服务器新增的工具在 manifest 中启用之前不可用。读操作无需确认即可执行；写操作会暂停会话（`always_ask`），服务器会强制执行来源追踪（provenance），并对 manifest 设定的任何策略施加上限（caps）。

- **Storefront 工具**（来自 `storefront` MCP 服务器）：`search_products`、`get_product_details`、`get_cart`、`add_to_cart`、`update_cart_item`、`remove_from_cart`、`get_preferences`、`save_memory`、`recall_memories`、`get_orders`、`get_order_status`、`search_policies`、`get_fulfillment_options`。
- **Presentation 工具**（由你的应用执行的自定义工具）：`present_products`、`present_comparison`、`present_plan`、`present_guide`、`present_order_status`、`checkout`、`present_suggestions`。

在内置的智能体工具中，只有 `read` 被启用；平台用它来加载技能内容。

## 保持 manifest 同步

清单引用了 `../../skills/`，因此对 skills 的修改会在下一次部署时生效。`system.md` 由 `shopping_agent.prompt` 生成，`agent.yaml` 中的自定义工具来自 `shopping_agent.tools.registry`；`scripts/check.py` 会将这两者以及上方的工具列表与其来源进行比对。MCP 服务器在启动时从 registry 读取其描述。

服务器的强制规则见 [`docs/safety.md`](../../docs/safety.md)；其 README 中的“身份（identity）”部分是生产部署需要修改的地方。
