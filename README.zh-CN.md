# Claude Commerce Agents

两个基于 Claude 构建的商业智能体：一个是**购物智能体（shopping agent）**，企业把它嵌进自家应用供顾客使用；另一个是**商家智能体（merchant agent）**，供员工运营后台。每个智能体只定义一次（提示词、技能、工具契约、门控），即可运行在 Messages API、Claude Agent SDK 和 Managed Agents 上；四个可运行的垂直场景在同一套库之上展示这两类智能体。

> [!NOTE]
> 这里所有公司、品牌、商品和人物均为虚构，唯一的公司是 ACME。没有任何东西会下单、刷卡或改动线上商品：`checkout` 只渲染购物车，交由宿主去完成；商家的每一次写操作都是暂存变更，直到有人批准才会落地。业务规则、授权与合规由部署方负责。

## 快速开始：运行演示

需要 Python 3.11+ 和 Node 22。克隆、安装、加 key、运行一个垂直场景：

```bash
git clone https://github.com/anthropics/commerce-agents.git && cd commerce-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt       # 七个包及其锁定依赖
cp .env.example .env                  # 填入 ANTHROPIC_API_KEY
(cd examples && npm ci)               # 八个 Web 应用共用一个 workspace
python scripts/run_demo.py retail     # API :8000 + 店面 :3000
```

`--merchant` 启动的是门户（portal）而非店面，`--all` 则两者都启动。垂直场景有 `retail`（:3000，门户 :3100）、`travel`（:3001，:3101）、`telecom`（:3002，:3102）和 `entertainment`（:3003，:3103）；每个 README 都列出了可在两个界面上尝试的提示词。

## 快速开始：构建你自己的智能体

Claude Code 插件可基于这些包、针对你的系统脚手架出一个智能体，或评审一个已有智能体。按上面的方式克隆仓库（插件会把它当作参考）：

```bash
claude plugin marketplace add anthropics/commerce-agents
claude plugin install commerce-builder@claude-commerce-agents
claude
/scaffold-commerce-agent a shopping assistant for our store
```

该命令会询问你的技术栈、回放计划并构建项目；`/add-commerce-flow` 和 `/author-commerce-evals` 可继续进行，`/review-commerce-agent` 则从一个已存在的智能体开始（见 [`plugins/commerce-builder/`](plugins/commerce-builder/)）。每个命令在请求匹配其描述时也会自动触发，所以并非必须显式点名。

## 两个智能体

**购物智能体**负责搜索、比较、规划、填充购物车、回答订单与政策问题，并记住客户告诉它的信息。它的五条流程就是 [`shopping-agent/skills/`](shopping-agent/skills/) 里的 skills；部署方需基于其目录、购物车、订单和政策系统实现 [`StorefrontBackend`](shopping-agent/core/shopping_agent/backend.py)。

**商家智能体**负责解读业绩、维护商品、处理库存与订单告警、定价促销、起草活动；每一次写操作都是暂存变更，由宿主的审批界面落地。它的五条流程是 [`merchant-agent/skills/`](merchant-agent/skills/) 里的 skills；部署方需基于其分析、目录、库存、定价和活动系统实现 [`MerchantBackend`](merchant-agent/core/merchant_agent/backend.py)。

## 目录布局

| 目录 | 内容 | pip 包名、`import` 名 |
|---|---|---|
| [`commerce-common/`](commerce-common/) | 两个角色共享的东西：config、fencing、memory、skills、grounding、presentation、executor 框架、事件 | `commerce-common`、`commerce_common` |
| [`shopping-agent/core/`](shopping-agent/core/) | 购物侧类型、`StorefrontBackend`、prompt、工具契约、gates、executor | `shopping-agent-core`、`shopping_agent` |
| [`shopping-agent/runtime-messages-api/`](shopping-agent/runtime-messages-api/) | `ShoppingAgent`，Messages API 上的回合循环 | `shopping-agent-runtime`、`shopping_agent_runtime` |
| [`shopping-agent/runtime-agent-sdk/`](shopping-agent/runtime-agent-sdk/) | Agent SDK 上的购物智能体，带一个控制台 | `shopping-agent-sdk`、`shopping_agent_sdk` |
| [`shopping-agent/managed-agents/`](shopping-agent/managed-agents/) | Managed Agents 的 manifest 与店面 MCP server | — |
| [`merchant-agent/core/`](merchant-agent/core/) | 商家侧类型、`MerchantBackend`、prompt、工具契约、变更护栏、gates、executor | `merchant-agent-core`、`merchant_agent` |
| [`merchant-agent/runtime-messages-api/`](merchant-agent/runtime-messages-api/) | `MerchantAgent` 与 Messages API 上的分析委托 | `merchant-agent-runtime`、`merchant_agent_runtime` |
| [`merchant-agent/runtime-agent-sdk/`](merchant-agent/runtime-agent-sdk/) | Agent SDK 上的商家智能体，带一个审批控制台 | `merchant-agent-sdk`、`merchant_agent_sdk` |
| [`merchant-agent/managed-agents/`](merchant-agent/managed-agents/) | Managed Agents 的 manifest、商家 MCP server、定时 digest | — |
| [`examples/`](examples/) | 四个垂直场景、共享宿主代码（`demo_common/`）、共享 Web 代码（`web-shared/`） | — |
| [`plugins/commerce-builder/`](plugins/commerce-builder/) | Claude Code 插件 | — |
| [`docs/`](docs/) | `safety.md`（强制规则）、`backends.md`（映射你的系统）、`deployment.md`（其他平台） | — |
| [`tests/`](tests/) | 跨包测试套件；每个包也有自己的 `tests/` | — |
| [`scripts/`](scripts/) | `install.sh`、`run_demo.py`、`smoke_chat.py`、`screenshot_tour.py`、`check.py`、`deploy_managed_agent.sh`、`verify_all.py` | — |

## 运行智能体的三种方式

**Messages API。** 参考循环；示例就是围绕它的宿主应用：

```python
from pathlib import Path

from shopping_agent import ShoppingAgentConfig
from shopping_agent_runtime import ShoppingAgent

agent = ShoppingAgent(backend=your_backend, skills_dir=Path("shopping-agent/skills"),
                      config=ShoppingAgentConfig(brand_name="Your Store"))
async for event in agent.stream_turn(messages, session, state):
    ...   # text_delta, tool_call, ui, cart_update（商家侧是 change_update）, turn_complete
await agent.update_memory(messages, session)   # 记忆抽取；仅此路径
```

示例宿主通过 `X-Session-Id` 头取会话 id。

**Agent SDK。** 同样的提示词、技能和工具，由 SDK 运行循环；宿主预取 grounding 所需的读取，回合结束后什么都不再运行：

```bash
python shopping-agent/runtime-agent-sdk/main.py --once "a two-person tent under $250"
python merchant-agent/runtime-agent-sdk/main.py          # 用 y/N 批准暂存变更
```

**Managed Agents。** 一个托管智能体，基于同样的技能与契约，调用你的 MCP server：

```bash
scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent   # 或 merchant-agent/...；--live 部署
```

## 安全

Fencing、来源门控（provenance gates）、caps、记忆校验和商家审批门控都在工具调用内部运行，且在三条路径上都成立；grounding、分析预算和记忆抽取属于运行时特性。[`docs/safety.md`](docs/safety.md) 逐条列出了每项规则及其模块、路径，以及部署方应首先补充的内容；示例没有鉴权，MCP server 绑定回环地址。

## 垂直场景

| 示例 | 店面 | 门户 |
|---|---|---|
| [`examples/retail/`](examples/retail/) ACME | 基于内置组件的搜索、比较、计划、购物车、checkout、记忆 | Digest、暂存的补货与商品修复、基于 SQL 视图的分析委托 |
| [`examples/travel/`](examples/travel/) ACME Travel | 日期绑定的库存与 `present_itinerary` 扩展 | 入住率日历与日期区间的价格调整 |
| [`examples/telecom/`](examples/telecom/) ACME Mobile | 账户上下文、计划矩阵、服务端撰写的费用披露 | 计划组合、写明受影响条目的调价、受保护的受监管费用 |
| [`examples/entertainment/`](examples/entertainment/) ACME Tickets | 计时持有、候补名单、转让、场馆地图、全包费用披露 | 活动节奏、增加真实容量的持有释放、保费用的调价 |

每个示例的 README 都有 `Try` 一节：`scripts/smoke_chat.py` 会跑的回合，以及若干单条提示词和"好的回答该是什么样"。

## 验证

```bash
ruff check . && ruff format --check . && pytest && python scripts/check.py
python scripts/verify_all.py                        # 上面这条加上部署 dry run 与 Web 构建
python scripts/smoke_chat.py --vertical travel      # 一次真实对话；需要 key
```

`requirements-dev.txt` 增加了 pytest 和 ruff。CI 在两个 Python 版本上从它安装，构建八个 Web 应用，并检查包名在公共 index 上仍未被注册（pin 文件从各自目录安装它们，绝不从 index）。要确认缓存，读取 `turn_complete` 的 `cache_read_input_tokens`，或每次模型调用在其 runtime 的 logger 上打印的那行：第二轮为 0 就说明前缀变了。

## 部署到其他平台

这些 runtime 接受任意 `anthropic` client 作为 `client=`，SDK runtimes 则从 CLI 环境取平台；[`docs/deployment.md`](docs/deployment.md) 覆盖 GCP Vertex AI、AWS Bedrock、Microsoft Foundry 和网关。

## MCP 连接器

本仓库不附带任何连接器；两个智能体都通过 backend 接口访问你的系统。凡官方连接器是权威数据源之处，它即是集成目标：分析数仓（Snowflake、BigQuery、Databricks、Amplitude）、财务（Stripe、Square、PayPal、QuickBooks）、配送（Slack、Google Drive、Gmail）。商务平台自身的目录/购物车/checkout MCP server 由某个 backend 方法在服务端调用；在 Managed Agents 上，manifest 把它挂在该角色的 server 旁边，而来源门控依旧守在每一次写操作之前。

## 让它成为你的

- **Backend 方法。** 每个方法都在服务端用宿主为该会话持有的凭据调用你的服务；模型只读结果。步骤有固定顺序的流程，要在 backend 里强制该顺序。
- **阅读 backend 指南。** [`docs/backends.md`](docs/backends.md) 讲解身份与凭据、有序流程、checkout、带选项的商品，以及你的平台无法提供的数字。
- **同一接口覆盖其他业务形态。** 在市场上，卖家是一个搜索维度，商家智能体以会话点名的 operator 身份行事。采用账户或合同定价时，报价即该会话账户的价格。没有自己的 checkout 时，关掉购物车，或把它交给报价单、采购订单或托管 checkout URL。
- **Checkout 做交接。** checkout 卡片链接到你自己的 checkout 路由，或平台的托管 checkout URL（市场上每个卖家一个）。backend 返回该 URL，宿主负责渲染；模型永远看不到它。
- **从小处着手。** 购物侧 pilot 只实现搜索和商品详情，其余打桩；打桩的方法返回一个 unavailable 结果，且不改动任何提示词字节。商家侧 pilot 实现八个读方法并让写操作拒绝；这样 digest 和指标就能在没有写路径的情况下运行。
- **关掉你没有的。** 企业完全没有的系统（推荐页面上没有购物车、没有订单跟踪）就是关掉一个 `enable_*` 开关，它会在每条路径上移除对应的工具、提示行和 grounding 规则；把需要它的流程挪到 `skills/_staged/` 下。商家 config 对商品编辑、库存、定价和活动有同样的开关。
- **添加你自己的。** 一条流程就是 `skills/` 下一个含 `SKILL.md` 的目录。领域 UI 是一个 `PresentationExtension`（垂直场景自带七个）。任一 config 上的 `brand_name`、`assistant_name` 和 `brand_voice` 用于设定身份。

## 许可证

Copyright 2026 Anthropic PBC。基于 [Apache License 2.0](./LICENSE) 授权。
这是参考实现；不再维护，也不接受贡献。
