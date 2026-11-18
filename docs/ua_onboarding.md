# Claude Commerce Agents — 新人上手指南

> 生成自 `.ua/knowledge-graph.json` · 分析 commit `790a108b` · 图谱规模 568 文件 / 1758 节点 / 3471 边 / 9 层 / 15 步导览（第 15 步为后补的生产就绪度指南）

## 1. 项目概览

**Claude Commerce Agents** 是两个基于 Claude 的商业智能体的参考实现：

- **购物智能体（shopping agent）**：商家嵌入自家应用、面向顾客，负责搜索、比价、规划、填购物车、回答订单与政策问题、记忆顾客偏好。
- **商家智能体（merchant agent）**：供员工运营后台，负责经营分析、维护商品、处理库存/订单告警、定价促销、起草活动；**每一次写入都是待人工审批的暂存变更**。

核心设计是「**一次定义，三种运行**」：提示词、技能、工具契约、护栏只定义一次，即可运行在 **Messages API**、**Claude Agent SDK**、**Managed Agents** 三条路径上；`examples/` 提供四个同一套库之上的可运行垂直演示（零售、旅游、电信、票务）。

| 维度 | 内容 |
|---|---|
| 框架 | FastAPI、Next.js、React |
| 主要语言 | Python、TypeScript（另有 CSS / JSON / YAML / TOML / Shell / Markdown 等 12 类被扫描收录） |
| Python 包 | `commerce-common`、`shopping-agent-core`、`merchant-agent-core` 及各自 runtime（messages-api / agent-sdk） |
| 前端 | 8 个 Next.js 应用 + 1 个 `web-shared` npm workspace |
| 规模 | 444 个代码文件节点、1021 函数、169 类、73 配置、50 文档、1 条 CI 流水线 |

> [!NOTE]
> 仓库中所有公司、品牌、商品与人物均为虚构（唯一公司 ACME）；不会真实下单、扣款或改动线上商品。示例无鉴权、MCP 服务器绑定回环地址。业务规则、授权与合规由部署方负责。

本地跑起来（README 口径）：

```bash
pip install -r requirements.txt && cp .env.example .env   # 填 ANTHROPIC_API_KEY
(cd examples && npm ci)
python scripts/run_demo.py retail                          # API :8000 + 店面 :3000
```

验证：`ruff check . && ruff format --check . && pytest && python scripts/check.py`

## 2. 架构分层（9 层）

依赖方向自上而下：垂直演示 → 示例宿主/共享基座 → 两个智能体核心 → 共享机制库。

| # | 层 | 文件数 | 职责 |
|---|---|---|---|
| 1 | **共享核心库层** | 35 | `commerce_common`：配置、围栏、记忆、技能、接地、呈现、执行框架、事件、轮次编排，含单测 |
| 2 | **购物智能体层** | 49 | core（领域模型/后端接口/门控/执行器）、runtime SDK、runtime Messages API、托管 MCP server、5 个技能 |
| 3 | **商家智能体层** | 59 | 同构但含变更台账、护栏、分析委托、定时摘要、merchant MCP server |
| 4 | **示例公共与宿主层** | 56 | `demo_common`（FastAPI 双智能体 HTTP 宿主、会话、记忆种子）、`web-shared`（API 客户端、事件类型、组件、图标） |
| 5 | **示例垂直演示层** | 331 | 四个行业演示：各自 storefront-web / merchant-web、数据 fixtures、垂直说明 |
| 6 | **Claude Code 插件层** | 13 | `commerce-builder` 插件：脚手架/评审/评测命令 + 5 个 SKILL.md 技能 |
| 7 | **项目文档层** | 5 | `README.md`、`CLAUDE.md`、`docs/{safety,backends,deployment}.md` |
| 8 | **配置与基础设施层** | 14 | 根依赖、CI 工作流、`scripts/` 运维脚本、`conftest.py` |
| 9 | **根级集成测试层** | 6 | `tests/`：跨包消费路径、平台接缝、角色注册表、搜索信封、系统开关、回合循环 |

关键文件（按「被引用次数 fan-in」挑出，改动它们影响面最大）：

- 共享库：`streaming.py`(11)、`fencing.py`(9)、`memory.py`(7)、`turn.py`(5)、`types.py`(5)
- 购物侧：`core/shopping_agent/types.py`(8)、`serialization.py`(6)、`config.py`(6)
- 商家侧：`core/merchant_agent/types.py`(10)、`config.py`(8)
- 示例宿主：`demo_common/__init__.py`(18)、`storefront_fixtures.py`(16)、`web-shared/protocol.ts`(8)
- 垂直前端：四个 `*/lib/types.ts`（13–21）是各自前端的类型契约中心

## 3. 关键概念

1. **后端接口是唯一集成面**：部署方只需实现 `StorefrontBackend` / `MerchantBackend`，把方法映射到自有目录、购物车、订单、策略 / 分析、库存、定价、活动系统；模型只读取返回结果，凭证留在宿主侧。换一家商家的成本几乎全落在这里。
2. **安全内建于工具调用，而非事后补丁**：围栏（fencing）、来源门控、上限（caps）、记忆写入校验、商家审批门控都跑在工具调用内部，且在三条运行路径上一致生效。`docs/safety.md` 逐条列出了代码强制规则、对模型的要求与部署方职责。
3. **暂存变更 + 人工审批**：商家侧 `StagedChange` 是关键抽象——改价、补货、上架都先成为待审批变更，由宿主预览卡片的按钮（`MERCHANT_REQUIRE_HOST_APPROVAL`）落地；模型绝不直接写库。
4. **围栏与接地**：`fencing.py` 清洗伪造轮次边界与转义注入；`grounding.py` 用词条/线索匹配强制模型先调用指定工具，再基于真实结果作答。
5. **技能即目录**：每个流程是含 `SKILL.md` 的目录，`SkillRegistry` 解析并渲染提示词索引，运行时无需读源码即可装载领域能力。
6. **生成式 UI**：`PresentationExtension` 定义建议卡片与 `ui_partial` 帧载荷；每个前端 `components/generative/` 下按呈现工具各有一个入口，由该应用 `lib/types.ts` 类型化——四个前端其实是同一套 payload schema 的四种构建，线上部署是第五种。
7. **提示缓存稳定性**：`prompt_assembly.py` 把缓存断点放在静态系统块、工具数组、最新持久化消息上；任何路径改动了提示/工具字节都会破坏前缀。验证方式是读 `turn_complete` 的 `cache_read_input_tokens`，第二轮为 0 即说明前缀变了。
8. **开关即移除**：业务上不具备的能力用 `enable_*` 开关关闭，会同时移除其工具、提示行与接地规则；对应流程移到 `skills/_staged/`。
9. **无凭证测试**：`commerce_common/testing.py` 提供 scripted 替身与 spy 记忆存储，`conftest.py` 提供内存假后端，保证 credential-free 的确定性测试。
10. **单 worker 与回环绑定**：会话、购物车、暂存变更都放在 `demo_common` 单进程内存里，因此示例只跑一个 worker。

## 4. 导览（15 步，来自图谱 tour）

| 步 | 标题 | 重点文件 |
|---|---|---|
| 1 | 项目概览：两个商业智能体 | `README.md` |
| 2 | 共享核心库 commerce-common | `__init__.py`、`config.py`、`turn.py` |
| 3 | 共享安全护栏：围栏、记忆与接地 | `fencing.py`、`memory.py`、`grounding.py` |
| 4 | 技能加载与 UI 展示扩展 | `skills.py`、`presentation.py` |
| 5 | 购物智能体：领域模型与后端接口 | `shopping-agent/core/.../types.py`、`backend.py` |
| 6 | 购物智能体的工具门控与执行循环 | `gates.py`、`executor.py` |
| 7 | 商家智能体：领域模型与暂存变更 | `merchant-agent/core/.../types.py`、`backend.py` |
| 8 | 商家护栏与暂存写入审批 | `merchant-agent/core/.../gates.py` |
| 9 | 参考循环运行时：Messages API | 两侧 `runtime-messages-api/.../orchestrator.py` |
| 10 | Agent SDK 与托管智能体 MCP 服务器 | `shopping_agent_sdk/agent.py`、两个 `*_mcp_server.py` |
| 11 | 示例宿主与共享前端基座 | `demo_common/host.py`、`web-shared/api.ts` |
| 12 | 一个端到端垂直示例：零售 | `retail/api/main.py`、`retail/storefront-web/app/page.tsx` |
| 13 | 用 Claude Code 插件脚手架你的智能体 | `plugin.json`、`scaffold-commerce-agent.md` |
| 14 | 安全规则与工程基础设施 | `docs/safety.md`、`.github/workflows/ci.yml`、`scripts/run_demo.py` |
| 15 | 生产环境就绪度与改进路线 | `docs/ua_prod_readiness.zh-CN.md` |

路径是递进的：先看整体地图 → 底层公共零件 → 安全约束 → 两个角色各一遍 → 三种运行时 → 拼成产品 → 落地一个垂直 → 脚手架复用 → 收尾看不可见但必须存在的规则。第 12 步读懂零售后，其余三个垂直只是换数据与换 UI 卡片。第 15 步把视角从"读懂系统"切到"把系统送上生产"：逐条列出部署方必须补齐的边界（认证、凭据、限流、业务规则、支付、记忆合规等）、需要重新设计的单进程状态，以及 P0/P1/P2 改进清单。

## 5. 文件地图（按层，精选）

**① 共享核心库层** — `commerce-common/commerce_common/`
`config.py` 基础配置 · `fencing.py` 文本/标签/卡片清洗 · `memory.py` 多种 MemoryStore + 写入过滤 + 事实抽取 · `skills.py` SkillRegistry · `prompt_assembly.py` 缓存断点与历史压缩 · `grounding.py` 强制工具匹配 · `presentation.py` 呈现载荷与 `enrich_partial` · `delegation.py` 隔离的委派任务 · `execution.py` 工具调度/失败阶梯/`split_status` · `streaming.py` AgentEvent/ToolOutcome/`to_sse` · `turn.py` 轮次辅助/历史压缩/即时工具分发 · `agent_sdk.py` 与 `mcp_server.py` 两条运行时的共享管线 · `manifest.py` 解析 Managed Agents 清单 · `testing.py` 测试替身 · `types.py` MemoryFact/MemoryCategory/ClockContext

**② 购物智能体层** — `shopping-agent/`
`core/shopping_agent/`：`types.py` 领域模型、`backend.py` StorefrontBackend、`config.py`、`gates.py` 加购来源门控、`executor.py` 工具 handler、`serialization.py` 统一围栏 payload、`fencing.py`、`__init__.py` 导出面 · `runtime-messages-api/` Messages API 回合循环 · `runtime-agent-sdk/` SDK 装配 · `managed-agents/storefront-mcp-server/` MCP 服务器 · `skills/` 五个流程

**③ 商家智能体层** — `merchant-agent/` — 与购物侧同构，`core/merchant_agent/` 另有 `changes.py`（变更台账/护栏/价格解析）、`analysis.py`（只读 SQL 校验与分析委托）、`enrichment.py`（快照与预览富化）、`gates.py`（apply/discard 来源校验）；`managed-agents/` 含定时摘要。

**④ 示例公共与宿主层** — `examples/demo_common/`：`host.py`（FastAPI 宿主、.env 加载、`X-Session-Id` 会话）、`sessions.py`、`storefront.py`、`merchant.py`、`memory.py`、`*_fixtures.py`（纯函数夹具）；`examples/web-shared/`：`api.ts`(AgentApi)、`protocol.ts`（镜像 `commerce_common/streaming.py`）、`ui.tsx`、`icons.tsx`、`format.ts`、session/turn hooks、`storefront/` 与 `portal/` 两个应用框架。

**⑤ 示例垂直演示层** — `examples/{retail,travel,telecom,entertainment}/`：`api/` 一个 FastAPI 进程（两个 mock 后端、agent_config、垂直路由与呈现扩展）、`data/` fixtures、`storefront-web/` + `merchant-web/` Next.js 应用。每个 Web 应用都有 `/showcase` 页面，从 `lib/showcase-fixtures.ts` 渲染组件，不需要 API 和密钥——改组件时先打开它。

**⑥ 插件层** — `plugins/commerce-builder/`：`commands/`（scaffold / add-flow / evals / review）、`skills/`（架构、评测、商家运营、提示缓存、信任安全）、`.claude-plugin/plugin.json`。

**⑦ 文档层** — `README.md`（总览）、`CLAUDE.md`（在本仓库工作的智能体指南）、`docs/backends.md`（后端对接）、`docs/deployment.md`（Vertex/Bedrock/Foundry/网关支持矩阵）、`docs/safety.md`（安全规则清单，部署前必读）。

**⑧ 配置与基础设施层** — `requirements*.txt`、`pytest.ini`、`ruff.toml`、`.github/workflows/ci.yml`（双 Python 版本跑 ruff+pytest、构建 8 个 Web 应用、校验包名未注册）、`scripts/{run_demo,smoke_chat,screenshot_tour,check,verify_all}.py`、`scripts/install.sh`、`deploy_managed_agent.sh`、`conftest.py`。

**⑨ 根级集成测试层** — `tests/`：`test_consumption_paths.py`（三条消费路径一致性）、`test_role_registries.py`（提示/工具字节一致性）、`test_system_switches.py`、`test_turn_loop.py`、`test_platform_seams.py`、`test_search_envelope.py`。

## 6. 复杂度热点

文件级复杂度分布：**simple 238 / moderate 209 / complex 121**（共 568）。`complex` 不等于「逻辑难」——本仓库里很大一部分是大型 TypeScript 类型集中文件与数据夹具，行数多但结构平铺。真正需要谨慎对待的是**高 fan-in + complex** 的组合，它们是改动会向外扩散的枢纽：

| 文件 | fan-in | 为什么小心 |
|---|---|---|
| `commerce-common/commerce_common/streaming.py` | 11 | 流式事件与 SSE 协议定义，全链路共享 |
| `commerce-common/commerce_common/memory.py` | 7 | 存储实现 + 写入过滤 + 事实抽取，安全边界 |
| `commerce-common/commerce_common/turn.py` | 5 | 轮次编排核心，三条运行路径共用 |
| `shopping-agent/core/.../gates.py`、`backend.py` | 4 | 加购来源门控 / 唯一集成面 |
| `merchant-agent/core/.../types.py`、`config.py`、`analysis.py`、`enrichment.py` | 10/8/4/3 | 商家领域模型集中，护栏阈值与 SQL 只读校验 |
| `examples/demo_common/storefront_fixtures.py` | 16 | 四个垂直的搜索/排序/过滤纯函数底座 |
| `examples/*/merchant-web/lib/types.ts` | 13–14 | 镜像后端 schema，前后端契约 |
| `examples/entertainment/api/ticketing.py` | 8 | 计时持有 / FIFO 候补 / 可撤销转让状态机 |
| `examples/web-shared/ui.tsx`、`format.ts` | 8 / 5 | 8 个 Web 应用共用的 UI 与格式化原语 |

**上手建议**：先按导览第 1–4 步读共享库，再挑一个垂直（推荐 `retail`）从头到尾走一遍；改动前先跑 `pytest` 基线，改 `lib/types.ts` 或 `protocol.ts` 时同步检查四个前端；任何涉及提示词/工具数组的改动都要复查提示缓存前缀是否仍稳定。准备上线时，直接跳到第 15 步的 `docs/ua_prod_readiness.zh-CN.md`，它把本文第 3 节第 2、10 条（安全内建、单 worker 限制）展开成了完整的生产改造清单。
