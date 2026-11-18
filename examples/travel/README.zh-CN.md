# ACME Travel（travel）

travel 示例让两个智能体跑在同一份日期绑定的住宿、航班和体验目录之上：店面为带日期的搜索报价、按天铺开行程、预订计划中的夜晚；门户展示供应商的每周入住率日历、暂存某个日期区间的房价调整，并从预览卡片应用它们。

## 运行

```bash
python scripts/run_demo.py travel               # API :8001 + 店面 :3001
python scripts/run_demo.py travel --merchant     # API :8001 + 门户 :3101
python scripts/run_demo.py travel --all          # 一个 API 上跑两个 Web 应用
```

或在 `examples/` 里执行 `npm ci` 后自行分别启动：

```bash
uvicorn travel.api.main:app --app-dir examples --reload --port 8001
(cd examples/travel/storefront-web && npm run dev)     # :3001
(cd examples/travel/merchant-web && npm run dev)       # :3101
```

聊天需要在仓库根 `.env` 或环境里提供 `ANTHROPIC_API_KEY`；浏览目录和门户组件不需要。`MERCHANT_REQUIRE_HOST_APPROVAL=0` 让聊天里的批准直接应用变更；默认由预览卡片的按钮来应用。

## 试试看

店面（`scripts/smoke_chat.py --vertical travel` 跑的是同样这三轮）：

1. Plan me a long weekend in Lisbon in mid-October — boutique stay, a couple of experiences, walkable neighborhood. Lay it out day by day.
2. Compare the stay you picked against a refundable alternative — what's the price difference for flexibility?
3. Add the refundable stay to my trip, and what does ACME Travel's cancellation window look like for it?

门户（`scripts/smoke_chat.py --vertical travel --merchant`；第三轮在卡片上批准变更前会被拒绝，最后两轮跟随批准）：

1. Home says two stays are pacing soft. Which two, how does their October look on the calendar, and where should rates move?
2. Ease the midweek rates by about ten percent on the two softest properties, but only for their soft October weeks. The rest of the calendar stays where it is. Show me the impact before anything goes live.
3. That works — approve it.
4. Now draft a shoulder-season campaign for those same two properties to go with the rate move: email to past guests, a modest budget of around $600. Stage it as a draft so I can read it first.
5. Which of our listings are losing us bookings on the page itself? If a description is thin, tell me which one; if the pages are fine, say so and tell me where the gap really is.

单条提示词，每条用新会话：

| 界面 | 提示词 | 好的回答 |
|---|---|---|
| Storefront | Show me refundable stays in Lisbon under $300 a night. | 一次搜索、一张卡片：Graca 套房是里斯本唯一既可变现退款又低于 $300 的住宿；Alfama 和 Baixa 客栈符合价格但不可退款，回答如实说明。 |
| Storefront | Two of us have $1,500 all-in for Lisbon: the nonstop from New York, three nights somewhere central, and one evening out. Does that work, and what would you book? | 按计划铺开两人航班、三晚住宿和一场夜间活动，加总后说明总额刚好略超 $1500 及超出多少，并提供能补齐差价的替换方案。 |
| Portal | Take the Baixa guesthouse's base rate down to $89 for the shoulder season. | 读取定价上下文：$89 是 29% 的变动，超过单次变更上限，因此不暂存；提供上限允许的最低基础价，或把 $89 作为淡季周带日期的促销。 |

## 本示例特有的部分

- `api/mock_travel.py`：基于 fixtures 的 `MockTravel`，即 `StorefrontBackend`。`travel_date` 过滤器作为可订性强制执行；带日期的结果就是一句报价：可退款时有 `free_cancellation_until`、`date_flex` 价格条，剩余三间及以下时有 `units_left_for_dates`。住宿的第一次 `add_to_cart` 会预订行程的计划夜晚（`TripPlan`）。
- `api/mock_merchant.py`：同一 `MockTravel` 之上、为入住率 fixture 中的住宿提供服务的 `MockTravelMerchant`，即 `MerchantBackend`。`stage_promotion` 是针对某日期区间的每晚房价变动，应用为价格覆盖；`stage_price_update` 改基础价，即目录价格。分析关闭。
- `api/itinerary.py`：注册 `present_itinerary`；每一天都从会话见过的商品填充，夜晚结构通过 `note_trip_plan` 记录。
- `api/occupancy.py`：注册 `present_occupancy_calendar`；智能体点名住宿和区间，每个数字都来自 `get_occupancy_calendar`。
- `api/agent_config.py`：两套配置。购物侧要求带日期的搜索提供 `travel_date`；商家侧把入住率术语加入 `metrics_intent_terms`，把 `nightly_rate` 加入 `price_bearing_fields` 和 `listing_update_blocked_fields`。
- `api/main.py`：带行程扩展的店面宿主，以及启动时由 `MemorySeeder` 从 `data/memory-seed.json` 重新填充的 `InMemoryMemoryStore`。
- `api/merchant.py`：`/overview` 上的 `today` 区块和 `/occupancy` 读取。
- `storefront-web/`、`merchant-web/`：本示例在 `../web-shared/` 之上的卡片、视图和 tokens。

## 数据

`data/catalog.json`、`users.json`、`orders.json`、`policies.json` 和 `memory-seed.json` 供给店面；`merchant_metrics.json`、`merchant_campaigns.json` 和 `merchant_messages.json` 供给门户；`merchant_occupancy.json` 同时供给两者：门户的日历和店面的剩余房间数。目录中没有照片。

会话与身份用的是 [`../demo_common/`](../demo_common/) 里的共享宿主代码：会话 id 代表一个 demo 档案或那位商家。
