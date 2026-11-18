# merchant-agent/managed-agents

商家智能体作为 Anthropic 托管的智能体，运行在 [Managed Agents API](https://platform.claude.com/docs/en/managed-agents/overview)（测试版）上。平台运行主循环并持有会话；技能、提示词和工具契约来自本仓库；你的后台系统保存在你自己托管的 MCP server 之后，该 server 暂存每一项变更，且只在平台的审批提示得到回答后才应用其中一项。智能体每次调用只能看到该服务器返回的内容，其他一概不可见。

```
your portal  ──user.message──►  hosted agent (agent.yaml: model, system.md, skills)
             ◄──agent.message, agent.custom_tool_use, requires_action──┘   │ MCP over HTTPS, credential from a vault
                                                                          ▼
                                    your infrastructure: merchant-mcp-server -> MerchantBackend
```

| 路径 | 内容 |
|---|---|
| `merchant-agent/agent.yaml` | 清单：5 个 skills、18 个商家工具、4 个 presentation 工具 |
| `merchant-agent/system.md` | 系统提示词，由 `merchant_agent.prompt.build_static_system` 生成；其头部列出了差异点 |
| [`merchant-mcp-server/`](merchant-mcp-server/) | 基于 `MerchantBackend` 的参考 MCP server；即你需要替换的部分 |
| [`scheduled-digest/`](scheduled-digest/) | 在 Messages API runtime 上、供任务调度器使用的无头 digest 运行 |
| `../../scripts/deploy_managed_agent.sh` | 解析清单（`commerce_common.manifest`）并上传；默认执行 dry run（空跑） |

## 快速开始

```bash
scripts/deploy_managed_agent.sh merchant-agent/managed-agents/merchant-agent     # 打印 /v1/agents 请求体

python merchant-agent/managed-agents/merchant-mcp-server/merchant_mcp_server.py
# 在 127.0.0.1:8201/mcp 提供服务；通过 HTTPS 隧道或你的网关访问它（见其 README）。

export ANTHROPIC_API_KEY=<API_KEY>
export MERCHANT_MCP_URL=https://<YOUR_HOST>/mcp
scripts/deploy_managed_agent.sh merchant-agent/managed-agents/merchant-agent --live
```

实时部署会上传五个 skills、创建智能体并打印其 id。会话需要一个 environment 以及一个保存了 MCP server 凭据的 vault；平台按 URL 将 vault 条目与清单中的服务器匹配。

```bash
H=(-H "content-type: application/json" -H "x-api-key: $ANTHROPIC_API_KEY"
   -H "anthropic-version: 2023-06-01" -H "anthropic-beta: managed-agents-2026-04-01")
curl -sS https://api.anthropic.com/v1/environments "${H[@]}" -d '{"name": "back-office",
  "config": {"type": "cloud", "networking": {"type": "limited", "allow_mcp_servers": true,
             "allowed_hosts": ["<YOUR_HOST>"]}}}'
curl -sS https://api.anthropic.com/v1/sessions "${H[@]}" -d '{"agent": "<AGENT_ID>",
  "environment_id": "<ENVIRONMENT_ID>", "vault_ids": ["<VAULT_ID>"]}'
```

然后向会话发送 `user.message` 事件并读取其事件流。

## 你的门户需要处理什么

- `agent.message`：助手文本；将其作为聊天内容渲染。
- `agent.custom_tool_use`：一次 presentation 工具调用。对照 `merchant_agent/tools/presentation.py` 校验 payload，用你自己的系统按 id 补全指标值、告警记录和变更 diff（`merchant_agent/enrichment.py` 是参考的关联逻辑），渲染后回复一个 `user.custom_tool_result`。每一次调用（包括 `present_suggestions`）都需要回复，否则会话会一直等待；此处模型在 chips 的结果之后写一句收尾文字，并用 `present_change_preview` 预览暂存变更。
- `session.status_idle` 且 `stop_reason: requires_action`：一个 `always_ask` 工具正在等待。对 `apply_change` 而言，变更已经在预览卡片上；操作者在那里的回答成为你的 `user.tool_confirmation`，server 收到后应用该变更。`save_memory` 同样暂停，所以要按工具名分派。

`merchant_agent/grounding.py` 中的 grounding 规则和 `merchant_agent/gates.py` 中的暂存跟进提醒不会在这条路径上运行，因为工具选择和回合由平台掌管；相关轮次由提示词规则覆盖。

## 工具权限

MCP 工具集默认拒绝（deny-by-default）：服务器新增的工具在 manifest 中启用之前不可用。读操作和 `stage_*` 工具无需确认即可运行，因为暂存只记录提案、不改变线上内容；`discard_change` 同样如此。`apply_change` 和 `save_memory` 是 `always_ask`，而 `apply_change` 上的暂停就是这条路径的审批界面：server 的 `default_config` 设置 `require_host_approval=False`，你传给 `build_server` 的 config 也必须这样设，否则每次 apply 都会被挂起。无论如何，来源和护栏检查在每次暂存和应用时都会运行。

- **商家工具**（来自 `merchant` MCP 服务器）：`get_business_snapshot`、`query_metrics`、`get_campaign_performance`、`search_listings`、`get_listing`、`get_inventory_alerts`、`get_order_issues`、`get_pricing_context`、`get_pending_changes`、`recall_memories`、`stage_listing_update`、`stage_price_update`、`stage_inventory_action`、`stage_promotion`、`stage_campaign`、`discard_change`、`save_memory`、`apply_change`。
- **Presentation 工具**（由你的门户执行的自定义工具）：`present_metrics`、`present_digest`、`present_change_preview`、`present_suggestions`。

在内置的智能体工具中，只有 `read` 被启用；平台用它来加载技能内容。`run_analysis` 不在这条路径上：manifest 不声明该工具，`system.md` 也不带分析规则。

## 保持 manifest 同步

清单引用了 `../../skills/`，因此对 skills 的修改会在下一次部署时生效。`system.md` 由 `merchant_agent.prompt` 生成，`agent.yaml` 中的自定义工具来自 `merchant_agent.tools.registry`；`scripts/check.py` 会将这两者以及上方的工具列表与其来源进行比对。MCP server 在启动时从 registry 读取其描述。

服务器的强制规则见 [`docs/safety.md`](../../docs/safety.md)；其 README 中的"身份（identity）"部分是生产部署需要修改的地方。
