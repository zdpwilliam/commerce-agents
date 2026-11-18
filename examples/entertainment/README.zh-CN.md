# ACME Tickets（entertainment）

entertainment 示例让两个智能体跑在同一套票务引擎之上：店面映射场馆座位图、逐项列出全包价、用服务端计时器持有门票、暂存 checkout，页面上带候补名单、票夹和转让；门户展示每场活动的销售节奏（pacing）、暂存持有释放、调价和促销，并从预览卡片把它们应用到店面所售的座位上。

## 运行

```bash
python scripts/run_demo.py entertainment               # API :8003 + 店面 :3003
python scripts/run_demo.py entertainment --merchant     # API :8003 + 门户 :3103
python scripts/run_demo.py entertainment --all          # 一个 API 上跑两个 Web 应用
```

或在 `examples/` 里执行 `npm ci` 后自行分别启动：

```bash
uvicorn entertainment.api.main:app --app-dir examples --reload --port 8003
(cd examples/entertainment/storefront-web && npm run dev)     # :3003
(cd examples/entertainment/merchant-web && npm run dev)       # :3103
```

聊天需要在仓库根 `.env` 或环境里提供 `ANTHROPIC_API_KEY`；浏览目录和门户组件不需要。`MERCHANT_REQUIRE_HOST_APPROVAL=0` 让聊天里的批准直接应用变更；默认由预览卡片的按钮来应用。

## 试试看

店面（`scripts/smoke_chat.py --vertical entertainment` 跑的是同样这三轮）：

1. I want two tickets to The Headliner show on the Friday night — somewhere with actual seats, not the pit. What are my tier options, all-in, and where do they put me in the room?
2. Before I commit — break down exactly what the lower bowl price is made of. What's the face value and what are the fees?
3. OK, hold two lower bowl tickets for me while I find my card.

门户（`scripts/smoke_chat.py --vertical entertainment --merchant`；第三轮在卡片上批准变更前会被拒绝，最后两轮跟随批准）：

1. How is the Friday Headliner show pacing against comparable events?
2. Release sixty of the promoter-hold seats on the Upper Terrace so they're on sale for the final stretch. Show me the release before it goes live.
3. Good — apply the release.
4. While we're on that tier: tag the Upper Terrace listing 'almost gone' and take its price up 15% for the final push. Stage both and show me before anything goes live.
5. Which shows sold the most tickets this week, and how does each compare with the week before? Put it on a card.

单条提示词，每条用新会话：

| 界面 | 提示词 | 好的回答 |
|---|---|---|
| Storefront | I can't make The Duo show anymore. Can you refund my two GA Floor tickets? | 读取退款政策：门票只在演出取消或改期时退款，而本场两者都不是；改为提供转让或转售挂单，自己绝不退款。 |
| Storefront | Is the Synth-Pop Act show really sold out, or is there anything left at all? | 搜索实时库存：每个售票档都显示剩余为零，两组粉丝转售票以全包价展示并标出高于票面的溢价；指向活动页面查看候补名单，不声称库存数字之外的稀缺性。 |

## 本示例特有的部分

- `api/ticketing.py`：两个后端共享的 `TicketingEngine`：`remaining()` 是容量减去已售、持有和挂售的票；持有在 `HOLD_TTL_S` 后过期；退货变成候补名单的 offer；转让保持可取消。它不收款。
- `api/mock_ticketing.py`：`MockTicketing`，即 `StorefrontBackend`：购物车就是会话的实时持有，`get_disclosure` 逐项列出费用，转售行带一个价值评分。
- `api/mock_merchant.py`：同一引擎之上的 `MockTicketingMerchant`，即 `MerchantBackend`：库存是开放数量，补货通过 `add_capacity` 释放持有的座位，调价保持费用行固定，暂停某档会抛 `ChangeNotApplicable`。
- `api/venue_map.py`：`present_venue_map`，各档座位及实时价格和数量。
- `api/hold_view.py`：`present_hold`，持有的条目和倒计时。
- `api/event_pacing.py`：`present_event_pacing`，各档售出率对照可比基线、持有桶、候补深度。
- `api/agent_config.py`：两套配置：开启披露，票务术语加入两个词表，费用行和票面值放进 `protected_fields`，分析关闭。
- `api/main.py`：持有、候补、票夹、转让和 demo 退货路由；引擎通知以 app 事件形式到达智能体。
- `api/merchant.py`：概览里的即将开演活动和 `/pacing` 读取。
- `storefront-web/`、`merchant-web/`：本示例在 `../web-shared/` 之上的卡片、视图和 tokens。

## 数据

`data/catalog.json`（无照片）、`inventory.json`（各档容量与已售）、`venues.json`、`tickets.json`（票夹）、`orders.json`、`policies.json`、`users.json` 和 `memory-seed.json` 供给店面；`merchant_metrics.json`、`merchant_pacing.json`（分配、历史、基线）、`merchant_campaigns.json` 和 `merchant_messages.json` 供给门户，其持有视图也读 `venues.json`。演出日期以 `catalog.json` 的 `dates_anchored_to` 为基准，启动时整体按周前移，同时推进 pacing 账簿和引用它们的订单行，使其始终领先于时钟（`api/mock_ticketing.py` 里的 `shift_event_dates`）。

会话与身份用的是 [`../demo_common/`](../demo_common/) 里的共享宿主代码：会话 id 代表一个 demo 档案或那位商家。
