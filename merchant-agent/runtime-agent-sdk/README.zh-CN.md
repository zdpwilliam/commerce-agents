# merchant-agent/runtime-agent-sdk（包名 `merchant_agent_sdk`）

基于 [Claude Agent SDK](https://pypi.org/project/claude-agent-sdk/) 的商家智能体。SDK 负责运行主循环、缓存与技能加载；本包提供与 `../runtime-messages-api/` 相同的静态提示词、skills、工具契约和执行器，外加一个审批控制台（approving console）。当你的宿主消费一个已完成的回合、并且你要在 SDK 的循环之上构建时，选择本包。

```
                 Claude Code CLI，由 SDK 启动
                 loop · caching · Skill 工具读取 .claude/skills/<flow>/SKILL.md
                            │  mcp__merchant__* 调用
                            ▼
   your process   merchant_tools.py: 基于 MerchantToolExecutor 的进程内 MCP server
                  agent.py: make_options() 构造选项；run_turn()  grounding、提醒、收集
                  MerchantBackend: 默认 MockRetailMerchant；生产环境用你自己的
```

## 配置

`scripts/install.sh` 安装本包及其依赖；`claude-agent-sdk` 打包了它启动的 CLI。凭据：`ANTHROPIC_API_KEY`，或一个已认证的 Claude Code 安装。其他平台：`docs/deployment.md`。

## 运行

```bash
python merchant-agent/runtime-agent-sdk/main.py                        # 与 mock 商店对话
python merchant-agent/runtime-agent-sdk/main.py --once "how did last week go"
```

控制台打印回复、每个 presentation payload（JSON 形式）、被调用的工具以及花费。在交互模式下它就是审批宿主：每回合之后，对本回合暂存的每项变更询问 `y/N`，`apply_change` 只对在该提示处获准的变更成功。`--no-host-approval` 设置 `require_host_approval=False`，于是在聊天里打字的批准就会应用变更；`--once` 没有可提示的地方，所以它暂存的变更保持暂存状态。在代码中：

```python
from claude_agent_sdk import ClaudeSDKClient
from merchant_agent_sdk import make_options, run_turn

options, toolset = make_options(backend=MyMerchantBackend())     # backend 默认为 mock
async with ClaudeSDKClient(options=options) as client:
    result = await run_turn(client, "Mark down the slow movers", toolset=toolset)
    result.text          # 回复
    result.ui            # [{"component": ..., "payload": ...}] 待渲染
    result.tool_calls    # 按调用顺序的工具名
    for change in toolset.pending_host_approvals():              # 已暂存，尚无标记
        if operator_approved(change):                            # 你的界面
            toolset.host_approve(change.change_id)               # 然后让智能体应用它
            ...
            toolset.host_clear(change.change_id)                 # 该回合返回后清除标记
```

`make_options` 还接受 `config`、`session_id`、`merchant_id`、`operator`、`max_turns` 和 `skills_dir`（用以替换 `../skills` 的项目自有 skills 目录）；`operator` 是 backend 在本对话暂存的变更上盖的戳。它返回的 toolset 持有该会话的 provenance 状态、审批标记和一个内存 `MemoryStore`；带持久化记忆的宿主可自行构造 `MerchantToolset(memory_store=...)`，并以 `agent.py` 的方式构造选项。

## 复用了什么

- **Skills**：`ensure_project_skills` 将 `../skills/*` 链接到本目录中、被 gitignore 的 `.claude/skills/`，并且选项允许这些名字使用 `Skill` 工具。`merchant_agent.prompt` 的静态提示词带有相同索引，外加 `SKILL_TOOL_ADAPTER`（`commerce_common/agent_sdk.py`），它让模型指向 `Skill` 而非 `load_skill`。
- **Tools**：`merchant_tools.py` 注册 `merchant_agent.tools.registry` 中的每个契约（除 `load_skill` 和 `run_analysis` 外，含描述与 schema），并通过 `MerchantToolExecutor` 执行每个调用。选项以 `permission_mode="dontAsk"` 将那些名字加入允许列表，并且除 `Skill`（以及启用分析时的委派传输 `Task`）外不挂载任何内置工具。
- **Backend**：任意 `MerchantBackend`，传入 `make_options`。

## 与 Messages API runtime 的差异

- **UI 在回合结束后才到达。** Presentation payload（包括暂存变更的预览卡片）通过 `result.ui` 返回；暂存变更从 `toolset.pending_host_approvals()` 读取，而非某个流事件。
- **回合收尾是一个 hook。** 一个工具批次后的 hook 在收尾组件上结束回合；在较旧的 CLI 上，则由模型写一句收尾文字替代。
- **Grounding 在宿主侧。** `run_turn` 运行指标和队列 grounding 规则所需的读操作，并将结果追加到消息中。
- **暂存提醒是第二遍。** 当一个变更请求以"什么都没暂存"结束时，`run_turn` 发送跟进提醒并合并结果。
- **分析是一个子 agent。** 开启 `enable_analysis` 时，`run-analysis` 在自己的上下文里基于读工具运行；config 上的分析预算不适用于它。
- **没有 Merchant context 块。** 商店上下文随工具结果到达（`get_business_snapshot`、`recall_memories`），且有一个工具描述被改写以说明这点。
- **此处未应用。** 记忆抽取（调用 `toolset.memory`）和 `thinking_effort`（设置 `options.effort`）。
- **没有游离上下文。** `make_options` 阻止 CLI 加载工作目录之上的任何 `CLAUDE.md`。
- **平台选择。** CLI 的环境；见 [`docs/deployment.md`](../../docs/deployment.md)。

## 测试

`pytest merchant-agent/runtime-agent-sdk/tests` 用脚本化的客户端在进程内调用已注册的工具，无需凭据；该测试套件还会把已注册的工具面与 `merchant_agent.tools.registry`、子 agent 的工具与 `ANALYSIS_READ_TOOLS` 比对，因此本包不会落后于 core。
