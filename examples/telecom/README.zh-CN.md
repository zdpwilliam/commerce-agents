# ACME Mobile（telecom）

telecom 示例让两个智能体跑在同一份运营商目录之上：店面用矩阵比较套餐、依据已登录账户回答升级问题、在套餐入购物车前展示其服务事实、暂存 checkout；门户读取流失率、展示各套餐的用户基数、暂存写明影响多少条线路的套餐调价，并从预览卡片应用它们。

## 运行

```bash
python scripts/run_demo.py telecom               # API :8002 + 店面 :3002
python scripts/run_demo.py telecom --merchant     # API :8002 + 门户 :3102
python scripts/run_demo.py telecom --all          # 一个 API 上跑两个 Web 应用
```

或在 `examples/` 里执行 `npm ci` 后自行分别启动：

```bash
uvicorn telecom.api.main:app --app-dir examples --reload --port 8002
(cd examples/telecom/storefront-web && npm run dev)     # :3002
(cd examples/telecom/merchant-web && npm run dev)       # :3102
```

聊天需要在仓库根 `.env` 或环境里提供 `ANTHROPIC_API_KEY`；浏览目录和门户组件不需要。`MERCHANT_REQUIRE_HOST_APPROVAL=0` 让聊天里的批准直接应用变更；默认由预览卡片的按钮来应用。

## 试试看

店面（`scripts/smoke_chat.py --vertical telecom` 跑的是同样这三轮）：

1. I keep blowing through my data — I've bought top-ups three months running. What plans would actually fit around 15GB a month? Show them side by side.
2. Am I eligible to upgrade my ACME Phone 4 yet? Show me what I could move to, and what the trade-in credit and early-upgrade terms would get me.
3. Switch me to the Unlimited plan and put it in my cart — and confirm there's no fee for changing plans mid-cycle.

门户（`scripts/smoke_chat.py --vertical telecom --merchant`；第三轮在卡片上批准变更前会被拒绝，最后两轮跟随批准）：

1. Show me churn by plan across the base. Which plan is bleeding, and since when?
2. Put a retention offer in front of the Essential lines that keep buying top-ups: a month of Plus 15GB at the Essential price if they move up. Stage it as a campaign to that cohort, app push, $1,500. Show me the draft before anything goes out.
3. That's fine — apply it.
4. Stock check while I'm here. Whatever device the alerts are flagging, stage a restock sized from its sell-through so we're covered for the next month. Preview first.
5. Where did last week's net adds come from against the week before? Put gross adds, deacts, port-ins and port-outs on one card and tell me what moved.

单条提示词，每条用新会话：

| 界面 | 提示词 | 好的回答 |
|---|---|---|
| Storefront | If the ACME Phone 3 I ordered isn't for me, how long do I have to send it back, and what would it cost me? | 读取订单和退货政策：手机尚未送达，所以 14 天窗口从送达起算；说明补货费以及已使用的预付费服务不退款。它不会发起退货。 |
| Storefront | Add a Roaming Day Pass to my cart for my trip next week. | 找到并加入该日票（一次搜索、一次加购），并说明一张日票从首次使用起覆盖一天，长途旅行每天都需要一张。 |
| Portal | Cut the Plus 15GB plan to $39 to stop the churn. Show me what it touches. | 读取定价上下文：$39 是 22% 的变动，超过单次变更上限，因此不暂存；提供 $40 作为最近的可永久价格，或 $39 作为带日期的促销，并给出该套餐承载的线路数和每条线路毛利。 |

## 本示例特有的部分

- `api/mock_telecom.py`：基于 fixtures 的 `MockTelecom`，即 `StorefrontBackend`，外加智能体每轮读取的账户上下文（`get_account_context`：升级资格、以旧换新、账单）和 `present_disclosure` 背后的服务事实（`get_disclosure`）。
- `api/mock_merchant.py`：同一 `MockTelecom` 之上的 `MockTelecomMerchant`，即 `MerchantBackend`。套餐的 `stock` 是其活跃线路，`stage_price_update` 和 `stage_promotion` 把它写进 `guardrail_notes`；套餐补货会抛 `ChangeNotApplicable`；已应用的变更写回店面。
- `api/plan_matrix.py`：在店面注册 `present_plan_comparison`；每个单元格都从会话见过的商品，加上订户的套餐和用量填充。
- `api/plan_mix.py`：从 `plan_mix_rows` 在门户注册 `present_plan_mix`。
- `api/agent_config.py`：两套配置。购物侧开启 `enable_disclosures` 并扩展 `policy_intent_terms`；商家侧扩展 `metrics_intent_terms`，并把受监管的费用字段放进 `protected_fields`。
- `api/main.py`：两个 demo 档案（订户 `demo-user`、潜在客户 `demo-user-2`）、从 `data/memory-seed.json` 播种的进程内记忆、加购按钮路由（仅设备和附加项），以及供店面外框使用的 `GET /api/account`。
- `api/merchant.py`：概览里的 `today_snapshot` 和门户的 `/base` 读取。
- `storefront-web/`、`merchant-web/`：本示例在 `../web-shared/` 之上的卡片、视图和 tokens。

## 数据

`data/catalog.json`、`users.json`、`orders.json`、`policies.json` 和 `memory-seed.json` 供给店面；`merchant_metrics.json`（每日基数变动）、`merchant_subscribers.json`（各套餐每周序列、资费表、群组）、`merchant_inventory.json`（设备库存）、`merchant_campaigns.json` 和 `merchant_messages.json` 供给门户。

会话与身份用的是 [`../demo_common/`](../demo_common/) 里的共享宿主代码：会话 id 代表一个 demo 档案或那位商家。
