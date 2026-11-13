# examples（示例）

四个垂直场景演示，每个都基于同一份商品目录运行两种 agent：`retail/`（ACME）、
`travel/`（ACME Travel，旅游）、`telecom/`（ACME Mobile，移动通信）、
`entertainment/`（ACME Tickets，票务）。运行 `python scripts/run_demo.py <vertical>`
可启动其中一个；每个垂直场景的 README 会列出其端口、可在两个界面上尝试的提示词，
以及它在基础库之上新增的内容。

## 目录结构

| 路径 | 内容 |
|---|---|
| `demo_common/` | 四个 API 共享的宿主代码：应用与中间件（`host.py`）、会话存储（`sessions.py`）、店面路由（`storefront.py`）、商家路由（`merchant.py`）、记忆路由与固件种子程序（`memory.py`）、模拟后端辅助（`*_fixtures.py`）|
| `web-shared/` | 八个 Web 应用共同导入的 npm 包：API 客户端、会话与轮次钩子、事件类型（`protocol.ts` 对应 `commerce_common/streaming.py`）、转录与检查器组件、共享原语与图标，以及两个应用框架（`storefront/`、`portal/`）|
| `package.json` | npm 工作区：包含 `web-shared` 以及每个 `*/storefront-web` 和 `*/merchant-web`（`npm ci` 会一次性安装全部）|
| `<vertical>/api/` | 一个 FastAPI 进程：两个模拟后端、两份 agent 配置（`agent_config.py`）、该垂直场景自身的路由与呈现扩展，以及挂载在 `/api/merchant` 下的商家路由 |
| `<vertical>/data/` | 两个后端加载的固件，列于该垂直场景的 README 中 |
| `<vertical>/storefront-web/`, `<vertical>/merchant-web/` | Next.js 应用：在本垂直场景的 `web-shared` 之上封装其卡片、视图与令牌 |

会话、购物车与暂存变更都存放在 `demo_common` 中一个进程的内存里，
因此示例只运行单个 worker。

`web-shared` 中只包含一份会话、流式与渲染管线。每个应用持有自己的组件：
`components/generative/` 下有每个呈现工具对应的一个入口，由应用的
`lib/types.ts` 进行类型约束，因此四个前端是同一套负载模式
（`shopping_agent/tools/presentation.py`、`merchant_agent/tools/presentation.py`）
的四种构建；线上部署的前端则是第五种构建。

## 展示页面（Showcase）

每个 Web 应用都提供 `/showcase` 页面，由 `lib/showcase-fixtures.ts` 渲染各自的组件；
它既不需要 API 也不需要密钥，演示启动后 `run_demo.py` 会打印店面的展示页 URL。
修改组件时打开它查看即可。

## 身份

店面会话从 `data/users.json` 中指定一个用户档案开始（`POST /api/session`）；
商家会话则绑定到该进程所服务的那一个商家。之后的每个请求只携带会话 id，
放在 `X-Session-Id` 中，路由据此读取主体（principal）。

## 环境变量

| 变量 | 作用 | 读取位置 | 默认值 |
|---|---|---|---|
| `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN` | 对话凭证；环境变量的优先级高于 `<vertical>/.env`，后者又高于仓库根目录的 `.env` | `demo_common/host.py` | 未设置（走客户端凭证链）|
| `COMMERCE_DEMO_AUTH` | 设为 `sdk` 时跳过 `.env` 文件并清除密钥变量，从而使用客户端的凭证链；`run_demo.py --federated` 会设置它 | `demo_common/host.py` | 未设置 |
| `DEMO_ALLOWED_HOSTS` | 除 `localhost` 和 `127.0.0.1` 外，API 响应的以逗号分隔的 Host 值 | `demo_common/host.py` | 未设置 |
| `DEMO_LOG_LEVEL` | `INFO` 为每个模型调用写一行；`DEBUG` 额外记录每个请求与响应 | `demo_common/host.py` | `INFO` |
| `MERCHANT_REQUIRE_HOST_APPROVAL` | `0` 允许在聊天中输入的审批直接应用变更；`1` 需要预览卡片上的按钮确认 | `demo_common/host.py` | `1` |
| `MERCHANT_ANALYSIS_CODE_EXECUTION` | `1` 在零售分析委派中挂载托管的代码执行工具 | `retail/api/agent_config.py` | `0` |
| `MERCHANT_ANALYSIS_MODEL` | 零售分析委派使用的模型 | `retail/api/agent_config.py` | 未设置（使用主模型）|
| `NEXT_PUBLIC_API_URL` | Web 应用发送请求的目标地址；`run_demo.py` 会将其设为 API 实际启动的端口 | `<app>/lib/api.ts` | `http://localhost:<API_PORT>` |

API 在启动时读取其变量；Web 应用则在构建时或开发服务器启动时读取 `NEXT_PUBLIC_` 变量。
