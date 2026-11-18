# commerce-builder（Claude Code 插件）

六个技能和四个命令，用于在本仓库的这些包之上构建一个购物智能体或商家智能体（[`../../README.md`](../../README.md)），或把已有的智能体迁移到它们之上。技能和命令都会在对话匹配其描述时加载，命令也可以显式键入；命令运行时会读取参考仓库（本 checkout、本地 clone 或新克隆的一份）。本插件自身不运行任何代码。

## 安装

```bash
claude plugin marketplace add anthropics/commerce-agents     # 或本地 clone 的路径
claude plugin install commerce-builder@claude-commerce-agents
```

## 命令

| 命令 | 作用 |
|---|---|
| [`/scaffold-commerce-agent`](commands/scaffold-commerce-agent.md) | 询问你的技术栈、回放计划，并基于参考包脚手架出一个购物智能体、商家智能体或两者 |
| [`/add-commerce-flow <flow>`](commands/add-commerce-flow.md) | 向已有智能体添加一条购物或商家流程：复制其 skill、接好它调用的工具、编写首批 eval 用例 |
| [`/author-commerce-evals`](commands/author-commerce-evals.md) | 构建 eval 套件：一个 runner、针对你自己目录的首批十个用例，以及供 CI 使用的回放门禁 |
| [`/review-commerce-agent`](commands/review-commerce-agent.md) | 梳理你已在运行的智能体，与参考逐行对比，并转换你选中的那些行 |

scaffold 和 review 会把学到的东西写进你项目的 `CLAUDE.md` 中 `## Commerce agent decision record` 之下；另外两个命令读取该节，而不是重新提问。

## 技能

| 技能 | 规则涉及 |
|---|---|
| [`commerce-architecture`](skills/commerce-architecture/) | 每次对话一个模型、backend 接口，以及一条规则属于哪一层（工具描述、提示词、skill） |
| [`commerce-prompt-caching`](skills/commerce-prompt-caching/) | 保持静态提示词和工具列表字节稳定，并检查请求是否命中缓存 |
| [`commerce-ui-tools`](skills/commerce-ui-tools/) | Presentation 工具、服务端富化、事件流，以及添加一个组件 |
| [`commerce-trust-safety`](skills/commerce-trust-safety/) | Fencing、来源与 caps、身份、门控状态、grounding、记忆写入、对抗性用例 |
| [`commerce-evals`](skills/commerce-evals/) | 用例形状、评分器、敌意 fixtures 和运行模式 |
| [`commerce-merchant-operations`](skills/commerce-merchant-operations/) | 暂存变更、护栏、宿主审批、指标 grounding 和市场（marketplace）范围界定 |

## 路径

1. `/scaffold-commerce-agent`，然后接好它打桩的 backend 方法；若已有智能体在运行，则用 `/review-commerce-agent` 及其转换的行。
2. 对 v1 索引里的每条流程使用 `/add-commerce-flow`。
3. `/author-commerce-evals`，并在每次提示词、技能或运行时改动后重新录制。
4. 按 [`../../docs/deployment.md`](../../docs/deployment.md) 部署。

鉴权，以及部署方欠其用户的记忆控制，由部署方接线；[`../../docs/safety.md`](../../docs/safety.md) 列出了它们。若本插件的文字与参考代码不一致，以代码为准。
