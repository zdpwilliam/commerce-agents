# ACME（retail）

retail 示例让两个智能体跑在同一份目录之上，只用内置组件：店面负责搜索、比较、规划、填充购物车、暂存 checkout，并在重启之间保留记忆；门户展示晨间 digest、暂存补货、商品修复和促销，并从预览卡片应用它们。它也是 SDK 控制台和参考 MCP server 默认加载的后端。

## 运行

```bash
python scripts/run_demo.py retail               # API :8000 + 店面 :3000
python scripts/run_demo.py retail --merchant     # API :8000 + 门户 :3100
python scripts/run_demo.py retail --all          # 一个 API 上跑两个 Web 应用
```

或在 `examples/` 里执行 `npm ci` 后自行分别启动：

```bash
uvicorn retail.api.main:app --app-dir examples --reload --port 8000
(cd examples/retail/storefront-web && npm run dev)     # :3000
(cd examples/retail/merchant-web && npm run dev)       # :3100
```

聊天需要在仓库根 `.env` 或环境里提供 `ANTHROPIC_API_KEY`；浏览目录和门户组件不需要。`MERCHANT_REQUIRE_HOST_APPROVAL=0` 让聊天里的批准直接应用变更；默认由预览卡片的按钮来应用。

## 试试看

店面（`scripts/smoke_chat.py --vertical retail` 跑的是同样这三轮）：

1. I'm taking my partner and our 6-year-old camping for the first time next month. We need a tent — nothing too heavy to deal with, ideally under $250.
2. Compare the top two options for me — mostly care about space and ease of setup.
3. The family one sounds right. Add it to my cart, and remind me what returns look like just in case.

门户（`scripts/smoke_chat.py --vertical retail --merchant`；第三轮在卡片上批准变更前会被拒绝，最后两轮跟随批准）：

1. What needs my attention this morning?
2. Restock the ocean wall decals with enough to cover the next month at the current pace, and fix that listing's description so it covers what's been missing. Show me both before anything goes live.
3. Looks right — approve the restock.
4. Kids-room decor feels like it's having a moment. Pull the numbers — is the under-the-sea line really outperforming the rest of the store this month?
5. Why did sales move over the last two weeks — which category or listings drove it, and by how much?

单条提示词，每条用新会话：

| 界面 | 提示词 | 好的回答 |
|---|---|---|
| Storefront | Order me the same resistance band set I bought from you before. | 在订单历史里找到该套装，加一件到购物车，并说明今天的价格与当时付款的价格不同。 |
| Storefront | Can I still return the yoga mat I ordered from you a while back? It's unused. | 读取订单和退货政策，从送达日期起算 30 天，说明窗口已过。它不会发起退货。 |
| Storefront | I need a universal travel adapter that can charge a laptop. | 只跑一次搜索、展示一张商品卡片（65 W 适配器），不发澄清问题。 |
| Storefront | Two couples, first weekend of car camping, and no gear between us. Put together what we need and keep the whole list under $600. | 按四人规划（一顶家庭帐篷、四个睡袋、一个炉具、一个保温箱），合计后说明总额超过 $600，并点名要去掉或共享什么才能压到预算内。 |
| Portal | Which category drove last week's change in sales, and by how much? | 读取快照和每日序列：儿童房是数据唯一拆出的品类，其增幅超过全店，因此其余品类下滑；说明数据没有完整的品类拆分。 |
| Portal | The ocean wall decals listing is missing wall coverage and material. Fill those in for me. | 读取 listing，发现记录里两个值都没有，于是请求用户提供，而不是把材质或覆盖面积写进页面。 |

## 本示例特有的部分

- `api/mock_retail.py`：基于 fixtures 的 `MockRetail`，即 `StorefrontBackend`，外加商品页展示的价格和评论摘要。
- `api/mock_merchant.py`：同一目录之上的 `MockRetailMerchant`，即 `MerchantBackend`；已应用的变更写回目录，`execute_analysis_query` 从同一状态的只读 SQLite 视图为分析委托提供服务。
- `api/agent_config.py`：两套配置。分析开启；`MERCHANT_ANALYSIS_CODE_EXECUTION=1` 增加托管沙箱，`MERCHANT_ANALYSIS_MODEL` 覆盖委托的模型。
- `api/main.py`：店面的文件持久化记忆存储（`data/.memory-store.json`）、商品详情富化和"加入购物车"按钮路由。
- `api/merchant.py`：概览里的 KPI 趋势和洞察卡片。
- `storefront-web/`、`merchant-web/`：本示例在 `../web-shared/` 之上的卡片、视图和 tokens。

## 数据

`data/catalog.json`、`users.json`、`orders.json`、`policies.json` 和 `memory-seed.json` 供给店面；`merchant_metrics.json`、`merchant_inventory.json`、`merchant_campaigns.json` 和 `merchant_messages.json` 供给门户。四件商品带选项（按尺寸的床垫、按尺寸和颜色的枕套、按色号的有色面霜、按重量的重力毯）：目录紧凑地编写它们的 variants，`demo_common` 派生其余部分，如 [`docs/backends.md`](../../docs/backends.md) 所述。`storefront-web/public/products/` 里的商品图片是 CC0 品类图，列在旁边的 `IMAGE-CREDITS.md`；没有图片的商品渲染为色块。

会话与身份用的是 [`../demo_common/`](../demo_common/) 里的共享宿主代码：会话 id 代表一个 demo 档案或那位商家。
