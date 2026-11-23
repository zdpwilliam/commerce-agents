# 恒信牙科医疗器械（零售示例）

零售示例用同一份牙科医疗器械商品目录同时驱动两个 Agent，且只使用内置组件：
门店端负责搜索、比较、方案搭配、填充购物车、暂存结算，并跨重启保留记忆；
商户端展示每日简报、暂存补货、商品信息修正与促销，并从预览卡片应用变更。
它也是 SDK 控制台和参考 MCP server 默认加载的后端。

## 运行

```bash
python scripts/run_demo.py retail               # API :8000 + 门店 :3000
python scripts/run_demo.py retail --merchant     # API :8000 + 商户后台 :3100
python scripts/run_demo.py retail --all          # 两个前端共用一个 API
```

也可以在 `examples/` 下执行 `npm ci` 后分别启动：

```bash
uvicorn retail.api.main:app --app-dir examples --reload --port 8000
(cd examples/retail/storefront-web && npm run dev)     # :3000
(cd examples/retail/merchant-web && npm run dev)       # :3100
```

对话功能需要在项目根目录的 `.env` 或环境中配置 `ANTHROPIC_API_KEY`；仅浏览商品目录和商户后台组件不需要。
`MERCHANT_REQUIRE_HOST_APPROVAL=0` 可让对话中的批准直接应用变更；默认情况下由预览卡片上的按钮应用。

## 体验

门店端（`scripts/smoke_chat.py --vertical retail` 会运行相同的三轮对话）：

1. 我想给诊所添置一台牙科种植手机，预算在 3000 元以内，最好扭矩可控、能高温高压灭菌。
2. 帮我对比一下前两个选项，主要看扭矩范围和接口兼容性。
3. 就选第一个吧，加入购物车，顺便提醒我退货政策是怎样的。

商户端（`scripts/smoke_chat.py --vertical retail --merchant`；第三轮在变更被批准前会被拒绝，最后两轮在批准之后）：

1. 今天有哪些需要我关注的事项？
2. 给种植手机补货，数量按当前销售速度覆盖未来一个月，并完善该商品的 description，把缺失的信息补全。先在预览里给我看，别急着上线。
3. 看起来没问题，批准补货。
4. 儿童牙科专区最近好像有起色，拉一下数据——这个月它的表现真的比店内其他品类好吗？
5. 过去两周销售额为什么变化——是哪个品类或商品带动的，影响多大？

单轮提问（每轮都是全新会话）：

| 界面 | 提问 | 好的回答 |
|---|---|---|
| 门店 | 把我上次买的那套车针再给我来一套。 | 从订单历史中找到该商品，加入购物车，并说明当前价格与上次购买时的价格不同。 |
| 门店 | 我之前买的光固化机还能退吗？还没拆封。 | 读取订单和退货政策，从送达日算起 30 天，说明窗口已过，且不发起退货。 |
| 门店 | 我需要一支能给手机充电的通用转接头。 | 只做一次搜索并展示一张商品卡片（65 W 转接头），不问澄清问题。 |
| 门店 | 我们诊所刚开张，需要配齐基础器械，整套预算控制在 5000 元以内。 | 按四人规模规划方案，汇总金额，说明总额已超预算，并指出可删减或共用的项目。 |
| 商户 | 上周销售额变化主要是哪个品类带动的，影响多大？ | 读取概览与每日序列：儿童牙科专区是唯一单独拆分的品类，涨幅高于全店，因此其余品类下滑；并说明数据没有完整的品类拆分。 |
| 商户 | 种植套件的商品信息缺少适用范围和材质，帮我补上。 | 读取商品，发现记录中两项都没有，于是询问用户，而不是自行编造材质或适用范围。 |

## 本示例特有的内容

- `api/mock_retail.py`：`MockRetail`（基于 fixtures 的 `StorefrontBackend`），以及商品详情页展示的价格与评价摘要。
- `api/mock_merchant.py`：`MockRetailMerchant`（基于同一目录的 `MerchantBackend`）；已应用的变更会写回目录，`execute_analysis_query` 从同一状态组成的只读 SQLite 视图为分析代理提供服务。
- `api/agent_config.py`：两个 Agent 配置。分析功能已开启；`MERCHANT_ANALYSIS_CODE_EXECUTION=1` 会启用托管沙箱，`MERCHANT_ANALYSIS_MODEL` 可覆盖代理模型。
- `api/main.py`：门店端基于文件的记忆存储（`data/.memory-store.json`）、商品详情增强，以及加入购物车按钮路由。
- `api/merchant.py`：概览页的 KPI 趋势与洞察卡片。
- `storefront-web/`、`merchant-web/`：本示例在 `../web-shared/` 之上的卡片、视图与设计变量。

## 数据

门店端由 `data/catalog.json`、`users.json`、`orders.json`、`policies.json` 和 `memory-seed.json` 提供数据；
商户端由 `merchant_metrics.json`、`merchant_inventory.json`、`merchant_campaigns.json`
和 `merchant_messages.json` 提供数据。共有四组商品带规格选项（种植套件按配置区分等）：
目录里紧凑地编写了这些变体，其余由 `demo_common` 派生，详见
[`docs/backends.md`](../../docs/backends.md)。
`storefront-web/public/products/` 下的商品图片是 CC0 授权图片，列在其旁的 `IMAGE-CREDITS.md` 中；
没有图片的商品以占位块呈现。

会话与身份使用 [`../demo_common/`](../demo_common/) 中的共享宿主代码：一个会话 id 对应一份演示用户档案或唯一的商户。
