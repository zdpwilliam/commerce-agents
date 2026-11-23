# commerce-agents

面向在本仓库工作的 Agent（包括 commerce-builder 插件用户）。这是 Claude 上商务 Agent 的公开参考实现：一个购物 Agent 和一个商家 Agent，各有三条运行路径，四个垂直行业示例，以及一个 Claude Code 插件。当前为纯中文项目，商店数据为牙科器械。

## 目录结构

- `commerce-common/commerce_common/`：两个角色共享的部分；其 `__init__` 列出各模块。
- `shopping-agent/core/shopping_agent/`：类型、`StorefrontBackend`、配置、提示词、`tools/`、门禁、enrichment、执行器。
- `merchant-agent/core/merchant_agent/`：商家的对应部分，外加 `changes.py` 和 `analysis.py`。
- `*/skills/`：每个角色五个流程，各有一个 `SKILL.md`。
- `*/runtime-messages-api/`：`ShoppingAgent`、`MerchantAgent`、商家分析代理。
- `*/runtime-agent-sdk/`：以 `ClaudeAgentOptions` 形式呈现的每个 Agent，带控制台。
- `*/managed-agents/`：清单目录（含派生的 `system.md`）和角色的 MCP server。
- `examples/demo_common/` 与 `examples/web-shared/`：垂直行业的 API 与 web 应用共享的部分；`examples/` 是 npm 工作区。
- `examples/<vertical>/`：`api/`、`data/`、`storefront-web/`、`merchant-web/`；端口 8000-8003、3000-3003、3100-3103。
- `plugins/commerce-builder/`：六个 skills、四个命令；`.claude-plugin/marketplace.json` 指向它。
- `docs/`：`safety.md`、`backends.md`、`deployment.md`。`scripts/`：install、demo、smoke、screenshots、check、deploy、verify。
- `tests/`：跨包套件（两个角色的全部三条路径）；每个包保留自己的 `tests/`。

`requirements.txt` 安装七个包及其固定依赖（`requirements-dev.txt` 增加 pytest 和 ruff）；`scripts/install.sh` 运行它。

## 设计规则

- 一个模型负责对话；规则按适用频率放在工具描述、提示词或 skill 中。
- 静态提示词和 `tools[]` 每轮字节相同；每请求数据放在断点之后的 fence 块中。
- UI 是 presentation 工具调用，在服务端校验并填充，以 `ui` 事件流式输出。
- 第三方内容是 fence 中的数据；写操作有 provenance 门禁且在上限内；`checkout` 不扣款；商家写操作仅通过宿主批准后生效。
- Core 与领域无关；垂直行业通过 `PresentationExtension` 添加 UI，其余部分自行维护。
- 每个机制只定义一次，位于 `commerce_common` 或某个角色 core 中，由三条路径共享。

## 虚构与原创

不出现真实的公司、品牌、商品或人物：唯一的公司是 ACME 及其产品线；每个品牌、提示词、schema 和数字都是在此原创的。两处例外：部署与集成目标（README 的「MCP 连接器」部分；`docs/deployment.md`、README 部署部分和平台测试中的平台与 SDK 名称），以及旁边 `IMAGE-CREDITS.md` 中列出的 CC0 类目图片。拿不准时，重新设计而非改名。

## 约定

- Python 3.11+，`ruff`（根目录 `ruff.toml`），`pytest`（根目录 `pytest.ini`），类型提示，`pydantic` schema；web 应用使用 Next.js 和 TypeScript。
- Skill 描述命名请求类别，不含示例话语；工具描述说明工具何时适用；示例保持示意性。
- 修改提示词文本、工具描述、skill 或 fence 提示会重新派生 `system.md`；`scripts/check.py` 对比它们。
- 行文：平实的陈述句；一个事物一个术语；每个事实只说一次并点明其模块；每个角色用各自的术语；README 说明某物是什么、如何运行、接口在哪；不写历史、日期或过程叙述；先删减再改风格。
- 新增模块要更新本文件及其 README。

## 验证

```bash
ruff check . && ruff format --check . && pytest && python scripts/check.py
python scripts/verify_all.py          # 额外包含部署 dry run 与 web 构建
```
