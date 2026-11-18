# 部署平台

代码默认调用 Anthropic API。每条运行路径都有一个地方，让部署改而指向 GCP Vertex AI、AWS Bedrock、Microsoft Foundry 或内部网关。这里的一切对两个角色都适用；示例用的是购物侧的名字，而 `MerchantAgent`、`merchant_agent_sdk` 和 `merchant-agent/managed-agents/` 一一对应地替换即可。

## 支持矩阵

| 路径 | Anthropic API | GCP Vertex AI | AWS Bedrock | Microsoft Foundry | 内部网关 |
|---|---|---|---|---|---|
| Messages API runtimes | 是 | 是 | 是 | 是 | 是 |
| Agent SDK runtimes | 是 | 是 | 是 | 是 | 是 |
| Managed Agents | 是 | 否 | 否¹ | 否 | 是² |
| 商家分析，托管代码执行 | 是 | 否 | 否 | 是³ | 否 |
| 商家分析，`execute_analysis_query` | 是 | 是 | 是 | 是 | 是 |

各路径如何选择平台：

| 路径 | 设置位置 | Anthropic API | GCP Vertex AI | AWS Bedrock | Microsoft Foundry | 内部网关 |
|---|---|---|---|---|---|---|
| Messages API runtimes | agent 上的 `client=` | 默认 | `AsyncAnthropicVertex` | `AsyncAnthropicBedrockMantle` 或 `AsyncAnthropicBedrock` | `AsyncAnthropicFoundry` | `AsyncAnthropic(base_url=..., auth_token=...)` |
| Agent SDK runtimes | `options.env` | 默认 | `CLAUDE_CODE_USE_VERTEX=1` | `CLAUDE_CODE_USE_BEDROCK=1` 或 `CLAUDE_CODE_USE_MANTLE=1` | `CLAUDE_CODE_USE_FOUNDRY=1` | `ANTHROPIC_BASE_URL` |
| Managed Agents | 部署脚本的 `ANTHROPIC_API_URL` | 默认 | — | — | — | `ANTHROPIC_API_URL` |

¹ 见下方的 AWS 说明。² 通过给部署脚本和 session 端点做透传代理；见"Managed Agents：端点"。³ 仅限托管在 Anthropic 上的 Foundry 部署。

两行分析适用于开启了 `enable_analysis` 的商家部署。托管代码执行（`analysis_use_code_execution`）挂载 `code_execution_20260120` server 工具，由 Anthropic API 提供；托管在 Anthropic 上的 Foundry 部署也提供它。`MerchantBackend.execute_analysis_query` 运行在你自己的基础设施里，返回一个普通工具结果，因此在任何地方都可用。retail 示例使用 query 方法，并且只在设置了 `MERCHANT_ANALYSIS_CODE_EXECUTION=1` 时挂载沙箱。

AWS 说明：Managed Agents 运行在 Anthropic 运营的基础设施上，因此没有 Vertex、Bedrock 或 Foundry 变体。在 AWS 上，它通过 [Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws) 提供，后者用 AWS 鉴权、一个 `anthropic-workspace-id` 头和一方模型 id 提供同样的 `/v1` 端点。部署脚本这两样都不发送；那条路线请遵循平台指南。

## 模型 id

模型是 config 里的一个字符串。每个角色的 config 都有 `model` 和 `memory_model`；商家 config 另加 `analysis_model`。SDK runtimes 把模型拷进它们的 options，manifests 在 `agent.yaml` 里设置它。没有别的地方读取这个字符串，所以换平台就是改 config。id 的语法因平台而异；请对照你平台的目录确认。

| 字段 | 仓库默认 | Anthropic API、网关 | GCP Vertex AI | AWS Bedrock（Mantle） | AWS Bedrock（Invoke API） | Microsoft Foundry |
|---|---|---|---|---|---|---|
| 购物 `model` | `claude-sonnet-5` | `claude-sonnet-5` | `claude-sonnet-5` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-sonnet-5` |
| 商家 `model` | `claude-opus-5` | `claude-opus-5` | `claude-opus-5` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-opus-5` |
| `memory_model` | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` | `claude-haiku-4-5@20251001` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-haiku-4-5` |

- Vertex 用 `@` 写带日期的快照。
- Bedrock 有两个端点。Mantle 说 Messages API，接受其自有阵容里不带日期的 `anthropic.` id；Invoke API 接受你账户目录里的 inference-profile id（带区域前缀、带日期、后缀 `-v1:0`）。
- Foundry 接受你资源里某个部署的名字；上面的值是默认值，匹配那些不带日期的一方 id。
- Managed Agents 接受一方 id。
- 三个模型字段都走同一个 client，所以三者都必须存在于目标平台上。

## Messages API runtimes：`client` 参数

`ShoppingAgent` 和 `MerchantAgent` 接受一个可选的 `client`。不提供时，它们构造 `AsyncAnthropic`，后者从环境读取 `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 和 `ANTHROPIC_BASE_URL`；导出后两个就把示例 API 指向一个网关。提供时，每次调用都用它：回合主循环（`messages.stream`）、记忆抽取和分析委托（`messages.create`）。`anthropic` 包里的任何 async client 都合适。该参数标注为 `AsyncAnthropic`，所以类型检查器对平台类需要一个 `cast`。

```python
from pathlib import Path

from anthropic import (
    AsyncAnthropic,
    AsyncAnthropicBedrockMantle,
    AsyncAnthropicFoundry,
    AsyncAnthropicVertex,
)
from shopping_agent import ShoppingAgentConfig
from shopping_agent_runtime import ShoppingAgent

common = dict(backend=your_backend, skills_dir=Path("shopping-agent/skills"))

# GCP Vertex AI: pip install "anthropic[vertex]"; Application Default Credentials.
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(memory_model="claude-haiku-4-5@20251001"),
    client=AsyncAnthropicVertex(project_id="your-project", region="global"),
)

# AWS Bedrock, Mantle endpoint: the standard AWS credential chain.
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(
        model="anthropic.your-served-model", memory_model="anthropic.claude-haiku-4-5"
    ),
    client=AsyncAnthropicBedrockMantle(aws_region="us-east-1"),
)

# Microsoft Foundry: an Azure API key, or azure_ad_token_provider= for Entra ID.
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(memory_model="claude-haiku-4-5"),
    client=AsyncAnthropicFoundry(resource="your-resource", api_key="your-azure-key"),
)

# In-house gateway: it must serve /v1/messages with SSE streaming.
agent = ShoppingAgent(
    **common,
    client=AsyncAnthropic(base_url="https://llm-gateway.internal.example", auth_token="your-token"),
)
```

这些包声明 `anthropic>=0.91`，即加入 `AsyncAnthropicBedrockMantle`（上面这些 client 类里最新的一个）的那个版本。

## Agent SDK runtimes：CLI 环境

SDK runtimes 不构造 HTTP client。`claude-agent-sdk` 启动 Claude Code CLI，由 CLI 从其环境选择平台。`make_options()` 返回 `(options, toolset)`；在打开 client 之前把平台变量加到 `options.env` 里。SDK 把 `env` 叠加到继承来的环境之上，所以只需列出平台变量。

```python
from claude_agent_sdk import ClaudeSDKClient
from shopping_agent_sdk import make_options

options, toolset = make_options()
options.env.update({"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "us-east-1"})
options.model = "us.anthropic.claude-sonnet-5"
async with ClaudeSDKClient(options=options) as client:
    ...
```

| 目标 | 必需 | 凭据 | 模型 id | 可选 |
|---|---|---|---|---|
| AWS Bedrock，Invoke API | `CLAUDE_CODE_USE_BEDROCK=1` | AWS 标准链 | inference-profile id | `ANTHROPIC_BEDROCK_BASE_URL` |
| AWS Bedrock，Mantle | `CLAUDE_CODE_USE_MANTLE=1` | AWS 标准链 | `anthropic.` id | `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`、`CLAUDE_CODE_SKIP_MANTLE_AUTH`⁴ |
| GCP Vertex AI | `CLAUDE_CODE_USE_VERTEX=1`、`ANTHROPIC_VERTEX_PROJECT_ID`、`CLOUD_ML_REGION` | Application Default Credentials | `@` 带日期的 id | `ANTHROPIC_VERTEX_BASE_URL` |
| Microsoft Foundry | `CLAUDE_CODE_USE_FOUNDRY=1`、`ANTHROPIC_FOUNDRY_RESOURCE` 或 `ANTHROPIC_FOUNDRY_BASE_URL` | `ANTHROPIC_FOUNDRY_API_KEY`，或通过 Azure 默认链的 Entra ID | 部署名 | `ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_DEFAULT_OPUS_MODEL`⁵ |
| 内部网关 | `ANTHROPIC_BASE_URL` | `ANTHROPIC_AUTH_TOKEN` 或 `ANTHROPIC_API_KEY` | 一方 id | `ANTHROPIC_CUSTOM_HEADERS` |

⁴ 当某个网关为请求签名时设为 `1`。⁵ 固定 CLI 用于其 Sonnet 与 Opus 调用的部署名。

当平台需要用自己的 id 来表示 CLI 的小模型调用时，设置 `ANTHROPIC_DEFAULT_HAIKU_MODEL`。这些变量属于 Claude Code；其文档是权威参考。

## Managed Agents：端点

`scripts/deploy_managed_agent.sh` 读取 `ANTHROPIC_API_KEY`，并 POST 到 `ANTHROPIC_API_URL`（默认 `https://api.anthropic.com`；另外两条路径读的是 `ANTHROPIC_BASE_URL`）。该地址上的网关必须代理 `/v1/skills`（multipart）、`/v1/agents`，并且对你的宿主应用，还要代理 `/v1/environments`、`/v1/sessions` 以及 session 事件流，同时保留 `anthropic-beta` 头。一个只代理 `/v1/messages` 的网关不服务这条路径。

```bash
# Dry run against a gateway (the default); add --live to deploy.
ANTHROPIC_API_URL=https://llm-gateway.internal.example \
  scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent
```

## 测试覆盖了什么

`tests/test_platform_seams.py` 用占位凭据构造每个平台的 client，检查两个 Messages API runtime 都绑定它，以及上面每个环境在两个 SDK runtime 里都到达 `ClaudeAgentOptions`。`scripts/verify_all.py` 跑两次部署 dry run。没有测试持有云凭据，因此这里不跑真实的平台对话；在依赖它之前，请在你自己的平台上跑一次。要在完全没有凭据的情况下驱动任一智能体，用 `commerce_common.testing.FakeClient` 模拟模型。
