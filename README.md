# Claude 商务 Agent

基于 Claude 构建的两个商务 Agent：一个是企业嵌入自有应用供顾客使用的**购物 Agent**，另一个是员工用于运营后台的**商家 Agent**。两者都只定义一次（提示词、skills、工具契约、门禁），即可运行在 Messages API、Claude Agent SDK 和 Managed Agents 三条路径上；四个可运行的垂直行业示例基于同一套库展示这两个角色。

> [!NOTE]
> 本项目中的公司、品牌、商品和人物均为虚构；唯一的公司是 ACME。
> 不会真正下单、扣款或修改线上商品：`checkout` 仅渲染购物车供宿主完成，商家的所有写操作都会暂存，直到人工批准才生效。业务规则、授权与合规由部署方负责。

## 快速开始：运行示例

需要 Python 3.11+ 和 Node 22。克隆、安装、添加密钥、运行某个垂直行业：

```bash
git clone https://github.com/anthropics/commerce-agents.git && cd commerce-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt       # 七个包及其固定版本的依赖
cp .env.example .env                  # 填入 ANTHROPIC_API_KEY
(cd examples && npm ci)               # 八个 web 应用共用一个工作区
python scripts/run_demo.py retail     # API :8000 + 商店 :3000
```

`--merchant` 启动商家后台而非商店，`--all` 同时启动两者。垂直行业有 `retail`（:3000，后台 :3100）、`travel`（:3001, :3101）、`telecom`（:3002, :3102）和 `entertainment`（:3003, :3103）；每个 README 都列出了可在两个界面上尝试的提问。

## 快速开始：构建你自己的 Agent

Claude Code 插件可基于这些包、面向你的系统脚手架生成一个 Agent，或审查已有 Agent。按上面的方式克隆仓库后（插件将其作为参考读取）：

```bash
claude plugin marketplace add anthropics/commerce-agents
claude plugin install commerce-builder@claude-commerce-agents
claude
/scaffold-commerce-agent a shopping assistant for our store
```

该命令会询问你的技术栈、回读方案并构建项目；`/add-commerce-flow` 和 `/author-commerce-evals` 在此基础上继续，`/review-commerce-agent` 则从已有 Agent 开始（[`plugins/commerce-builder/`](plugins/commerce-builder/)）。当请求与命令描述匹配时，这些命令也会自动运行，因此显式命名是可选的。

## 两个 Agent

**购物 Agent** 负责搜索、比较、规划、填充购物车、回答订单与政策问题，并记住顾客告诉它的内容。它的五个流程即 [`shopping-agent/skills/`](shopping-agent/skills/) 中的 skills；部署方基于自己的商品、购物车、订单和政策系统实现 [`StorefrontBackend`](shopping-agent/core/shopping_agent/backend.py)。

**商家 Agent** 负责解读经营表现、维护商品、处理库存与订单预警、定价促销以及起草活动；每次写操作都是暂存的变更，需宿主的审批界面应用才生效。它的五个流程即 [`merchant-agent/skills/`](merchant-agent/skills/) 中的 skills；部署方基于自己的分析、商品、库存、定价和活动系统实现 [`MerchantBackend`](merchant-agent/core/merchant_agent/backend.py)。

## 目录结构

| 目录 | 内容 | pip 包名、`import` 名称 |
|---|---|---|
| [`commerce-common/`](commerce-common/) | 两个角色共享的部分：配置、fencing、记忆、skills、grounding、presentation、执行器框架、事件 | `commerce-common`, `commerce_common` |
| [`shopping-agent/core/`](shopping-agent/core/) | 购物类型、`StorefrontBackend`、提示词、工具契约、门禁、执行器 | `shopping-agent-core`, `shopping_agent` |
| [`shopping-agent/runtime-messages-api/`](shopping-agent/runtime-messages-api/) | `ShoppingAgent`，Messages API 上的回合循环 | `shopping-agent-runtime`, `shopping_agent_runtime` |
| [`shopping-agent/runtime-agent-sdk/`](shopping-agent/runtime-agent-sdk/) | Agent SDK 上的购物 Agent，带控制台 | `shopping-agent-sdk`, `shopping_agent_sdk` |
| [`shopping-agent/managed-agents/`](shopping-agent/managed-agents/) | Managed Agents 的清单与商店 MCP server | — |
| [`merchant-agent/core/`](merchant-agent/core/) | 商家类型、`MerchantBackend`、提示词、工具契约、变更护栏、门禁、执行器 | `merchant-agent-core`, `merchant_agent` |
| [`merchant-agent/runtime-messages-api/`](merchant-agent/runtime-messages-api/) | `MerchantAgent` 及 Messages API 上的分析代理 | `merchant-agent-runtime`, `merchant_agent_runtime` |
| [`merchant-agent/runtime-agent-sdk/`](merchant-agent/runtime-agent-sdk/) | Agent SDK 上的商家 Agent，带审批控制台 | `merchant-agent-sdk`, `merchant_agent_sdk` |
| [`merchant-agent/managed-agents/`](merchant-agent/managed-agents/) | 清单、商家 MCP server、Managed Agents 的定时摘要 | — |
| [`examples/`](examples/) | 四个垂直行业、共享宿主代码（`demo_common/`）、共享 web 代码（`web-shared/`） | — |
| [`plugins/commerce-builder/`](plugins/commerce-builder/) | Claude Code 插件 | — |
| [`docs/`](docs/) | `safety.md`（强制规则）、`backends.md`（映射你的系统）、`deployment.md`（其他平台） | — |
| [`tests/`](tests/) | 跨包测试套件；每个包也有自己的 `tests/` | — |
| [`scripts/`](scripts/) | `install.sh`、`run_demo.py`、`smoke_chat.py`、`screenshot_tour.py`、`check.py`、`deploy_managed_agent.sh`、`verify_all.py` | — |

## 运行 Agent 的三种方式

**Messages API.** 参考循环；示例是围绕它构建的宿主应用：

```python
from pathlib import Path

from shopping_agent import ShoppingAgentConfig
from shopping_agent_runtime import ShoppingAgent

agent = ShoppingAgent(backend=your_backend, skills_dir=Path("shopping-agent/skills"),
                      config=ShoppingAgentConfig(brand_name="Your Store"))
async for event in agent.stream_turn(messages, session, state):
    ...   # text_delta, tool_call, ui, cart_update (商家侧为 change_update), turn_complete
await agent.update_memory(messages, session)   # 记忆提取；仅此路径
```

示例宿主通过 `X-Session-Id` 请求头传递会话 id。

**Agent SDK.** 相同的提示词、skills 和工具，由 SDK 运行循环；宿主预取 grounding 读取，回合结束后不再执行任何操作：

```bash
python shopping-agent/runtime-agent-sdk/main.py --once "预算 500 元以内的牙科种植手机"
python merchant-agent/runtime-agent-sdk/main.py          # 用 y/N 批准暂存的变更
```

**Managed Agents.** 基于相同 skills 与契约的托管 Agent，调用你的 MCP server：

```bash
scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent   # 或 merchant-agent/...；--live 表示部署
```

## 安全

Fencing、provenance 门禁、上限、记忆校验和商家审批门禁都在工具调用内部执行，并在三条路径上生效；grounding、分析预算和记忆提取是运行时特性。[`docs/safety.md`](docs/safety.md) 逐条列出规则及其模块与路径，以及部署方应首先补充的内容；示例没有认证，MCP server 绑定到回环地址。

## 垂直行业

| 示例 | 商店 | 后台 |
|---|---|---|
| [`examples/retail/`](examples/retail/) ACME 牙科 | 基于内置组件的搜索、比较、方案、购物车、结算与记忆 | 摘要、暂存补货与商品修正、基于 SQL 视图的分析代理 |
| [`examples/travel/`](examples/travel/) ACME Travel | 按日期绑定的库存与 `present_itinerary` 扩展 | 入住率日历与按日期区间的调价 |
| [`examples/telecom/`](examples/telecom/) ACME Mobile | 账户上下文、套餐矩阵、服务端生成的费用披露 | 套餐结构、注明受影响线路的调价、受监管费用保护 |
| [`examples/entertainment/`](examples/entertainment/) ACME Tickets | 定时占座、候补名单、转让、场馆地图、全包费用披露 | 活动节奏、释放真正增加容量的占座、保费调价 |

每个示例的 README 都有 `Try` 部分：`scripts/smoke_chat.py` 运行的回合，以及单个提问与好的回答示例。

## 验证

```bash
ruff check . && ruff format --check . && pytest && python scripts/check.py
python scripts/verify_all.py                        # 上一行外加部署 dry run 与 web 构建
python scripts/smoke_chat.py --vertical travel      # 一次真实对话；需要密钥
```

`requirements-dev.txt` 增加 pytest 和 ruff。CI 基于它在两个 Python 版本上安装、构建八个 web 应用，并检查包名未在公共 index 注册（固定文件从各自目录安装，绝不从 index 安装）。要确认缓存，可从 `turn_complete` 读取 `cache_read_input_tokens`，或查看各运行时 logger 中每次模型调用打印的那一行：第二轮为零表示前缀发生了变化。

## 部署到其他平台

运行时接受任意 `anthropic` 客户端作为 `client=`，SDK 运行时从 CLI 环境获取平台；[`docs/deployment.md`](docs/deployment.md) 涵盖 GCP Vertex AI、AWS Bedrock、Microsoft Foundry 和网关。

## MCP 连接器

不附带任何连接器；两个 Agent 都通过 backend 接口访问你的系统。当官方连接器是数据来源时，它就是集成目标：分析数仓（Snowflake、BigQuery、Databricks、Amplitude）、财务（Stripe、Square、PayPal、QuickBooks）、投递（Slack、Google Drive、Gmail）。商务平台自带的商品、购物车或结账 MCP server 由 backend 方法在服务端调用；在 Managed Agents 上，清单将它挂载在角色 server 旁边，provenance 门禁仍位于每次写操作之前。

## 定制成你的项目

- **Backend 方法。** 每个方法都在服务端用宿主为该会话持有的凭据调用你的服务；模型只读取结果。步骤顺序固定的流程在 backend 中强制该顺序。
- **阅读 backend 指南。** [`docs/backends.md`](docs/backends.md) 讲解身份与凭据、有序流程、结账、带选项的商品，以及你的平台无法提供的数字。
- **同一接口覆盖其他业务形态。** 在 marketplace 上，卖家是一个搜索维度，商家 Agent 代表会话指定的运营方行事。使用账户或合同价时，报价即该会话账户的价格。没有自己的结账时，可关闭购物车，或将其交给报价、采购单或托管结账 URL。
- **结账交由外部完成。** 结账卡片链接到你的结账路由，或平台的托管结账 URL（marketplace 上每个卖家一个）。backend 返回 URL，宿主渲染它；模型永远看不到它。
- **从小处着手。** 购物试点实现搜索和商品详情，其余打桩；打桩方法返回不可用结果，且不改变任何提示词字节。商家试点实现八个读方法并让写操作拒绝；这样摘要和指标在没有写路径的情况下也能运行。
- **关闭你没有的系统。** 企业完全不具备的系统（推荐页面无购物车、无订单跟踪）通过关闭 `enable_*` 开关实现，这会在所有路径上移除其工具、提示词行和 grounding 规则；把需要它的流程放到 `skills/_staged/`。商家配置对商品修改、库存、定价和活动有相同的开关。
- **添加你自己的。** 一个流程就是 `skills/` 下带 `SKILL.md` 的目录。领域 UI 是 `PresentationExtension`（示例附带七个）。任一配置上的 `brand_name`、`assistant_name` 和 `brand_voice` 设定身份。

## 许可证

Copyright 2026 Anthropic PBC。依据 [Apache License 2.0](./LICENSE) 授权。
这是参考实现；不再维护，也不接受贡献。
