# 部署平台

代码默认调用 Anthropic API。每条运行路径都有一个位置，供部署方改为指向 GCP Vertex AI、AWS Bedrock、Microsoft Foundry 或内部网关。这里的一切对两个角色都适用；示例使用购物侧的命名，而 `MerchantAgent`、`merchant_agent_sdk` 和 `merchant-agent/managed-agents/` 一一替换即可。

## 支持矩阵

| 路径 | Anthropic API | GCP Vertex AI | AWS Bedrock | Microsoft Foundry | 内部网关 |
|---|---|---|---|---|---|
| Messages API 运行时 | 是 | 是 | 是 | 是 | 是 |
| Agent SDK 运行时 | 是 | 是 | 是 | 是 | 是 |
| Managed Agents | 是 | 否 | 否¹ | 否 | 是² |
| 商家分析，托管代码执行 | 是 | 否 | 否 | 是³ | 否 |
| 商家分析，`execute_analysis_query` | 是 | 是 | 是 | 是 | 是 |

各路径如何选择平台：

| 路径 | 设置位置 | Anthropic API | GCP Vertex AI | AWS Bedrock | Microsoft Foundry | 内部网关 |
|---|---|---|---|---|---|---|
| Messages API 运行时 | Agent 上的 `client=` | 默认 | `AsyncAnthropicVertex` | `AsyncAnthropicBedrockMantle` 或 `AsyncAnthropicBedrock` | `AsyncAnthropicFoundry` | `AsyncAnthropic(base_url=..., auth_token=...)` |
| Agent SDK 运行时 | `options.env` | 默认 | `CLAUDE_CODE_USE_VERTEX=1` | `CLAUDE_CODE_USE_BEDROCK=1` 或 `CLAUDE_CODE_USE_MANTLE=1` | `CLAUDE_CODE_USE_FOUNDRY=1` | `ANTHROPIC_BASE_URL` |
| Managed Agents | 部署脚本的 `ANTHROPIC_API_URL` | 默认 | — | — | — | `ANTHROPIC_API_URL` |

¹ 见下方 AWS 说明。² 通过部署脚本和 session 端点的透传代理；见「Managed Agents：端点」。³ 仅限托管在 Anthropic 上的 Foundry 部署。

两个分析行适用于开启 `enable_analysis` 的商家部署。托管代码执行（`analysis_use_code_execution`）挂载 `code_execution_20260120` server 工具，由 Anthropic API 提供；托管在 Anthropic 上的 Foundry 部署也提供它。`MerchantBackend.execute_analysis_query` 在你的基础设施中运行并返回普通工具结果，因此处处可用。retail 示例使用查询方法，仅在设置 `MERCHANT_ANALYSIS_CODE_EXECUTION=1` 时挂载沙箱。

AWS 说明：Managed Agents 运行在 Anthropic 运营的基础设施上，因此没有 Vertex、Bedrock 或 Foundry 变体。在 AWS 上，它通过 [Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws) 提供，以 AWS 认证、`anthropic-workspace-id` 请求头和一方模型 id 提供相同的 `/v1` 端点。部署脚本两者都不发送；该路由请遵循平台指南。

## 模型 id

模型是配置中的字符串。每个角色配置有 `model` 和 `memory_model`；商家配置另有 `analysis_model`。SDK 运行时将模型复制到其 options 中，清单在 `agent.yaml` 中设置它。没有其它地方读取该字符串，因此迁移平台就是改配置。id 语法因平台而异；请对照你的平台目录确认。

| 字段 | 仓库默认值 | Anthropic API、网关 | GCP Vertex AI | AWS Bedrock (Mantle) | AWS Bedrock (Invoke API) | Microsoft Foundry |
|---|---|---|---|---|---|---|
| 购物 `model` | `claude-sonnet-5` | `claude-sonnet-5` | `claude-sonnet-5` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-sonnet-5` |
| 商家 `model` | `claude-opus-5` | `claude-opus-5` | `claude-opus-5` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-opus-5` |
| `memory_model` | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` | `claude-haiku-4-5@20251001` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-haiku-4-5` |

- Vertex 用 `@` 写入带日期的快照。
- Bedrock 有两个端点。Mantle 使用 Messages API，接受其自身阵容中不带日期的 `anthropic.` id；Invoke API 接受你账户目录中的推理配置 id（带区域前缀、带日期、后缀 `-v1:0`）。
- Foundry 接受你资源中部署的名称；上面的值是默认值，与不带日期的一方 id 一致。
- Managed Agents 接受一方 id。
- 三个模型字段都经过同一个 client，因此三者都必须存在于目标平台上。

## Messages API 运行时：`client` 参数

`ShoppingAgent` 和 `MerchantAgent` 接受可选的 `client`。不提供时，它们构造 `AsyncAnthropic`，从环境读取 `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 和 `ANTHROPIC_BASE_URL`；导出后两个变量会让示例 API 指向网关。提供时，每次调用都使用它：回合循环（`messages.stream`）、记忆提取和分析代理（`messages.create`）。`anthropic` 包中的任何异步 client 都适用。该参数标注为 `AsyncAnthropic`，因此平台类需要 `cast`。

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

# GCP Vertex AI: pip install "anthropic[vertex]"; 使用应用默认凭据。
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(memory_model="claude-haiku-4-5@20251001"),
    client=AsyncAnthropicVertex(project_id="your-project", region="global"),
)

# AWS Bedrock, Mantle 端点：标准 AWS 凭据链。
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(
        model="anthropic.your-served-model", memory_model="anthropic.claude-haiku-4-5"
    ),
    client=AsyncAnthropicBedrockMantle(aws_region="us-east-1"),
)

# Microsoft Foundry：Azure API key，或用 azure_ad_token_provider= 走 Entra ID。
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(memory_model="claude-haiku-4-5"),
    client=AsyncAnthropicFoundry(resource="your-resource", api_key="your-azure-key"),
)

# 内部网关：必须以 SSE 流式提供 /v1/messages。
agent = ShoppingAgent(
    **common,
    client=AsyncAnthropic(base_url="https://llm-gateway.internal.example", auth_token="your-token"),
)
```

这些包声明 `anthropic>=0.91`，即加入 `AsyncAnthropicBedrockMantle`（上述 client 类中最新的一个）的版本。

## Agent SDK 运行时：CLI 环境

SDK 运行时不构造 HTTP client。`claude-agent-sdk` 启动 Claude Code CLI，CLI 从其环境选择平台。`make_options()` 返回 `(options, toolset)`；在打开 client 前将平台变量加入 `options.env`。SDK 会在继承的环境上叠加 `env`，因此只需列出平台变量。

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
| AWS Bedrock, Invoke API | `CLAUDE_CODE_USE_BEDROCK=1` | AWS 标准凭据链 | 推理配置 id | `ANTHROPIC_BEDROCK_BASE_URL` |
| AWS Bedrock, Mantle | `CLAUDE_CODE_USE_MANTLE=1` | AWS 标准凭据链 | `anthropic.` id | `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`、`CLAUDE_CODE_SKIP_MANTLE_AUTH`⁴ |
| GCP Vertex AI | `CLAUDE_CODE_USE_VERTEX=1`、`ANTHROPIC_VERTEX_PROJECT_ID`、`CLOUD_ML_REGION` | 应用默认凭据 | 带 `@` 日期的 id | `ANTHROPIC_VERTEX_BASE_URL` |
| Microsoft Foundry | `CLAUDE_CODE_USE_FOUNDRY=1`、`ANTHROPIC_FOUNDRY_RESOURCE` 或 `ANTHROPIC_FOUNDRY_BASE_URL` | `ANTHROPIC_FOUNDRY_API_KEY`，或通过 Azure 默认链走 Entra ID | 部署名称 | `ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_DEFAULT_OPUS_MODEL`⁵ |
| 内部网关 | `ANTHROPIC_BASE_URL` | `ANTHROPIC_AUTH_TOKEN` 或 `ANTHROPIC_API_KEY` | 一方 id | `ANTHROPIC_CUSTOM_HEADERS` |

⁴ 当网关为请求签名时设为 `1`。⁵ 固定 CLI 用于 Sonnet 和 Opus 调用的部署名称。

当平台需要自己的 id 用于 CLI 的小模型调用时，设置 `ANTHROPIC_DEFAULT_HAIKU_MODEL`。这些变量属于 Claude Code；其文档即参考。

## Managed Agents：端点

`scripts/deploy_managed_agent.sh` 读取 `ANTHROPIC_API_KEY` 并 POST 到 `ANTHROPIC_API_URL`（默认 `https://api.anthropic.com`；另外两条路径读取 `ANTHROPIC_BASE_URL`）。该地址的网关必须代理 `/v1/skills`（multipart）、`/v1/agents`，以及为你的宿主应用代理 `/v1/environments`、`/v1/sessions` 和 session 事件流，并保持 `anthropic-beta` 请求头不变。只代理 `/v1/messages` 的网关不服务此路径。

```bash
# 对网关做 dry run（默认）；加 --live 表示部署。
ANTHROPIC_API_URL=https://llm-gateway.internal.example \
  scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent
```

## 测试覆盖范围

`tests/test_platform_seams.py` 用占位凭据构造每个平台的 client，检查两个 Messages API 运行时都绑定它，以及上述每个环境在两条 SDK 运行时中都能到达 `ClaudeAgentOptions`。`scripts/verify_all.py` 运行两次部署 dry run。没有测试持有云凭据，因此这里不运行真实的平台对话；在依赖它之前请在你的平台上跑一次。要完全无需凭据地驱动任一 Agent，可用 `commerce_common.testing.FakeClient` 为模型编写脚本。
