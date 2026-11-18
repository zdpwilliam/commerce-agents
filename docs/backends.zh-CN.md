# 后端：映射你自己的系统

`StorefrontBackend` 和 `MerchantBackend` 把你自己的系统翻译成智能体读取的记录。本指南涵盖身份与凭据、有序流程、checkout、带选项的商品，以及缺失的数字。每个角色的 `backend.py` 和 `types.py` 里的方法 docstring 即是契约。retail 与 telecom 示例展示了这一切的实际运行。

## 第 1 步：确定调用者是谁、以及如何鉴权

**在会话开始时绑定身份。** 你的宿主对调用者做鉴权，并用其解析出的 principal 启动会话：购物智能体用 customer id，商家智能体用 merchant id 与 operator。每个 backend 方法都收到那个会话对象，并从中读取身份。没有任何路由、也没有任何工具参数携带 user id。

**让凭据与身份待在一起。** 你的 backend 为该 principal 调用自有平台所需的任何东西，都跟着会话走，绝不跟着模型走：

- 每个客户一个 token：把它放在会话 context 的一个子类上，或放进一个由宿主在登录时填充、backend 按 customer id 读取的存储里。
- 一个服务凭据：把它传给 backend 的构造函数。

**把访客当作一个 principal。** 将会话标记为 guest。当某个读操作需要一个账户（订单历史、已保存地址）时，抛出一个由你的 executor 子类翻译成"请客户登录"的异常。当访客登录时，启动一个新会话。示例宿主在会话开始时取一个 demo profile id，作为真实登录的替身。

**在 Managed Agents 上，** 平台在 vault 里为每个 MCP server 持有一个凭据，而你的 MCP server 从已鉴权的请求中推导出客户。携带每客户身份的方式是：每个客户会话一个 vault 凭据，或一个由你的网关在每个请求上校验的、带签名的声明。

## 第 2 步：让多步流程保持有序

有些流程只有按顺序才有意义：先验证身份，再检查资格，然后提交；先持有座位，再确认。backend 强制这个顺序。

1. 把流程的状态保存在 backend 里，以会话为键。
2. 当某个调用在它所依赖的步骤之前到达时，抛出你自己的异常类。
3. 在一个 executor 子类里映射那个类（`domain_error`），让工具结果点名缺失的步骤，而不是读起来像系统故障。模型随后告诉客户先做什么。
4. 对于一个你的平台会去重的写操作，从会话 id 和购物车条目的哈希推导出一个幂等键。
5. 当客户在对话之外完成了一个步骤（支付页面、验证码）时，让宿主在该会话上排队一个 app 事件；下一回合读取它。

entertainment 示例的票务引擎正是用这种方式强制持有上限、过期和所有权，其 executor 子类把引擎的消息转达给模型。

## 第 3 步：决定 checkout 如何完成

`checkout` 工具结束智能体的部分：它渲染购物车。本仓库中没有任何东西下单或收款。为 checkout 卡片选择三种交接方式之一：

| 你的情况 | 卡片做什么 | 你实现什么 |
|---|---|---|
| Checkout 是你自己 App 里的一条路由 | 链接到那条路由 | 什么都不做；适用默认行为 |
| 平台托管的 checkout（购物车 API 无法在服务端收款） | 打开平台的托管 checkout URL | `checkout_handoff` 为该购物车返回 URL |
| 每个卖家分别 checkout 的市场 | 每个卖家显示一个链接 | `checkout_handoff` 每个卖家返回一个条目 |

executor 在模型调用之后把 `checkout_handoff` 返回的内容加到卡片 payload 里，因此 URL 从不经过模型。示例卡片只链接 `https` URL。支付完成后，排队一个 app 事件，让下一回合知道。

## 第 4 步：映射带选项的商品

一条商品或 listing 记录是三种形态之一：

| 形态 | 如何识别 | 智能体如何用它 |
|---|---|---|
| Plain（普通） | 没有 options | 搜索返回它；购物车、价格更新和补货用它的 id |
| Family（商品族） | 有 `options`，例如 size: twin、queen、king | 搜索返回它；详情列出其 variants。购物车、价格和补货写操作需要 variant id；暂停、促销和内容编辑可以点名该商品族 |
| Variant（变体） | 有 `option_values`（每个 option 一个值）和 `variant_of`（商品族的 id） | 在其商品族的详情里返回，带自己的 id、价格和库存；购物车、价格更新和补货用它的 id |

variant 的 id 在一切原本放商品或 listing id 的地方使用；没有单独的 variant-id 字段。商品族 id 与 variant id 共享一个命名空间，所以如果父级的平台 id 可能等于子级的，就在你的 backend 里给商品族 id 加前缀。搜索既匹配 option 值也匹配属性，所以像 size = king 这样的过滤器可用。一个已经从查询里解析出每个 option 的 backend 可以直接从搜索返回 variant；否则搜索返回商品族。

**从常见目录模型映射。**

| 你的目录 | 商品族 | 变体 | 普通 |
|---|---|---|---|
| 父记录与子记录；父记录不可购买 | 父记录：其 id、内容和作为 options 的变异属性 | 每个子记录：id、价格、库存、option 值、父 id | 一个独立商品 |
| 每行都是一个可购买的 SKU；兄弟行共享一个 group key（购物 feed） | 合成：以前缀化的 group key 作为 id、首行的标题与图片、从各行收集的 options；详情解析该 id | 每一行，以合成 id 作为其商品族 | 一个没有 group 的行 |
| 一个总是带 variants 的商品外壳；价格和库存只在 variants 上 | 该商品：id、内容、option 名称和值 | 每个 variant | 一个单 variant 商品，以该 variant 的 id 提供，不带 options |

```text
your platform                              this record
product  P-88  "Trail Tee"                 {"product_id": "P-88", "title": "Trail Tee", "price": 24.0,
  option  size: S M L                       "options": {"size": ["S", "M", "L"]}}
  variant V-1  S  24.00  12 in stock       details.variants[0] = {"product_id": "V-1", "price": 24.0,
  variant V-2  M  24.00   0 in stock         "in_stock": true, "option_values": {"size": "S"},
  variant V-3  L  26.00   4 in stock         "variant_of": "P-88"}  … and V-2, V-3
```

**什么不是 variant。**

- 每次请求计算出的价格或库存（搜索日期的每晚房价、按人数的票价、一个座位）。请求的维度作为搜索过滤器进来，返回的记录是该情境下的一句报价。travel 示例以这种方式给住宿定价。一个房型分别备货和定价的预订引擎，仍可以把它们列为某个 property 的 variants。
- 差异不止在 option 值上的兄弟项（有各自区域和费用的票档；有各自额度的计划档）。把它们保留为按某属性分组的独立记录，就像 entertainment 示例那样。
- 一个由多个卖家以不同价格出售的商品。一条记录只有一个价格：返回你会出售的那个 offer，或把每个 offer 列为独立记录。
- 按订单生产的商品、捆绑包和带修改项的菜单项。这些选择随请求属性或在你自己的购物车扩展里传递，由 backend 定价。
- 按实测重量计价的商品。数量按整件计，所以按固定包装出售，而这些包装本身可以是 variants。

**一个商品族自己的数字。**

- 店面价格是最低的有货 variant 的价格（一个"起"价）；只要任一 variant 有货，该商品族就有货。
- 门户价格是最低 variant 的价格，无论是否有货，这样某个尺码售罄时目录不会显示变动；库存是各 variant 之和。门户从 pricing context 读取每个 variant 的区间。
- 标题、描述和图片描述的是商品族。一个 variant 可以覆盖它继承的任何字段（某个颜色有自己的图片）。在商品族的详情里，每个 variant 是一行紧凑记录：id、option 值、价格、库存，以及只有那些不同的字段。
- 只有列出的 variants 存在。如果 king/blush 那一行不存在，该产品就不以 king/blush 出售；智能体如实说明并提供最近的在列 variant。

**多少个 variants。** 详情在一个带围栏的结果里返回商品族的全部 variant，上限为 `max_fenced_chars`（默认 12,000 字符）。一行紧凑记录约 70 到 120 字符，所以一个商品族最多约六十个 variant。更大的矩阵按首个 option 拆成每个商品族：一款八个颜色、十四个尺码的鞋变成八个"每族十四个"的商品族。超过上限时结果会被截断而不报错，所以用你最大的商品族核对一下。

**缺货。** 当 `add_to_cart` 点名一个存在但不可购买的 variant 时，抛出 `Unavailable`，其消息只包含 id：什么缺货，以及哪些兄弟 variant 有货。executor 转达它，且什么都不写。retail 与 telecom 示例就是这么做的。对商店根本不卖的东西，用 `NotOffered` 和 `enable_*` 开关。

## 第 5 步：把商家写操作应用到商品族

| 写操作 | 点名 | 在商品族 id 上 |
|---|---|---|
| 价格更新 | 一个 variant | 由 executor 持有，它指向各 variant id；"所有尺码涨 5%"是每个 variant 一个条目 |
| 补货 | 一个 variant | 同样持有 |
| 暂停或激活 | 任一 | 让所有 variant 下架或重新上架 |
| 促销 | 任一 | 展开为每个 variant 一行，各有自己的前后价；每行都计入每次变更的条目上限 |
| 内容编辑 | 任一 | 编辑共享内容；一个 variants 共享商品族内容字段的 backend 会拒绝在 variant 上改那些字段，如 retail 示例 |

如果你的领域用另一个字段名计价（每晚房价、票价），把它加到 merchant config 的 `price_bearing_fields` 里，否则价格上限不会被检查。

## 第 6 步：对你的平台无法提供的数字返回 `None`

绝不要返回一个替代性的零。返回 `None`，并用一句简短的 note 说明原因。

| 位置 | 返回什么 |
|---|---|
| 经营快照 | 对缺少的流量、转化率或平均订单价值返回 `None`；note 说明缺哪个 |
| 指标序列 | 一个空序列，附一条说明原因的 note |
| 活动 | 对渠道不报告的支出或收入返回 `None` |
| Pricing context | `min_price_basis`：底价是该商品的成本还是一条商店规则 |
| 库存告警、订单问题 | 当平台没有这类对象时，从库存和订单派生告警与问题；只给能算出的种类 |
| 商家上下文 | 一个 `limitations` 列表（每条给出来源和一句话），用于全店范围的缺口，例如订单历史过短 |

retail 商家示例返回两条 limitations：90 天的订单历史，以及一个不报告收入的邮件渠道。

## 在示例中看它

- Retail 目录：一个按尺码的床垫（一个尺码缺货、价格分档）、一套按尺码和颜色的枕套（一种组合缺货）、六色一价的有色面霜，以及一条描述里写明"如何选重量"规则的重力毯。
- Telecom 目录：一部按存储和颜色的手机，每个 variant 有分期方案。
- Fixtures 在商品族下紧凑地编写 variants；共享加载器补齐其余并派生 options。线上形态就是详情工具返回的东西。
- Retail 与 telecom 的 `merchant_inventory.json` 持有对应的 variant 行；retail 商家上下文展示 `limitations`；entertainment 示例展示固定顺序的流程。
