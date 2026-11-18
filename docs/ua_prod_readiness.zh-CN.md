# 生产环境就绪度分析：问题、缺陷与改进建议

> 基于知识图谱 commit `821b1f87` 与当前源码分析。图谱与 HEAD 一致、工作区无漂移。
> 适用的安全规则权威清单见 [`safety.md`](safety.md)；本文在其基础上做"上生产"视角的归纳与补充。

## 0. 结论先行

本项目是一份**参考实现（reference implementation）**，README 明确写着 "not maintained and does not accept contributions"。它的定位是演示"一次定义、三种运行"，**不是开箱即用的生产系统**。

"上生产"的本质不是修若干 bug，而是**把参考实现刻意留空的边界补实**。好消息是：这些边界被 `safety.md` 的 "What a deployment owns" 一节列得非常清楚，工作量可精确估算。真正需要从架构层面重新设计的只有 **一处**（单进程内存状态）；其余约 90% 是按清单补齐的工程工作。

安全设计有一个根本性的二分（[`safety.md:42-59`](safety.md)）：

- **确定性保证**（围栏 fencing、来源 provenance、上限 caps、记忆校验、宿主审批）内建在 executor 的**工具调用内部**，三条路径通吃，任何模型都成立。
- **概率性保证**（提示词约束、grounding 的"先读"、政策条款等）依赖模型遵循指令，且**并非三条路径都强制**。

生产事故最常见的来源，是把后者误当成前者。

---

## 1. 部署方必须补齐的硬缺口（P0）

这些是 `safety.md:61-86` 明确要求部署方负责、参考实现里刻意留空的部分。不补完不应暴露给真实用户。

| 缺口 | 参考实现现状 | 生产必须做什么 |
|---|---|---|
| **认证与授权** | 示例接受任何调用者；MCP server 接受任何能连上的连接 | 每条路由 + 两个 MCP server 的鉴权；loopback 之外必须前置认证网关 |
| **凭据** | 宿主从会话解析，模型只读结果 | backend 调用自有服务的凭据不能进模型；接入 vault/密钥管理 |
| **速率限制** | 无 | 聊天路由前的滥用控制（防刷、配额、并发上限） |
| **业务规则** | gates 只查 provenance 与 caps | 欺诈、资格、定价、库存规则写进 `StorefrontBackend` / `MerchantBackend`——**gate 决定"能不能写"，backend 决定"该不该发生"** |
| **支付** | `checkout` 只渲染购物车，仓库无任何支付逻辑 | 在宿主应用完成下单扣款；仓库不碰支付凭据 |
| **记忆即个人数据** | 写入过滤、保留期、0o600 文件权限（`memory.py:319-320`） | 事实类别策略、保留期、**查看/删除入口**、接入账户注销流程 |
| **日志卫生** | 每次模型调用一行 INFO（会话 id 仅摘要）；DEBUG 记请求/响应体 | DEBUG 含全部注入事实与整个购物车，需按个人数据施加同等保留期与访问控制 |
| **审批界面** | gate 只检查"宿主是否设置了批准标记" | 真实审批 UI 与"谁能批准"的权限模型 |
| **护栏取值** | 两个 `config.py` 的值是演示值 | 按真实业务重置价差、批量上限、促销深度、预算等 |

---

## 2. 代码与架构层面的已知限制

### 2.1 单进程内存状态 —— 唯一需要"重新设计"的点

会话、购物车、暂存变更台账、provenance 都在 `examples/demo_common/sessions.py` 的进程内存里（图谱：`SessionStore` 用 `dict[str, tuple[int, dict]]` 存状态）。`memory.py` 的 `JsonFileMemoryStore` 也只是单文件。

- **后果**：只能跑一个 worker；多实例部署会状态分裂；进程重启丢状态。
- **改造**：把会话/购物车/台账/provenance/记忆外置到 Redis 或数据库，加跨实例并发控制（现有写锁只在单进程内串行化）。这是从 demo 到生产**唯一无法靠"补配置"解决、必须动架构**的地方。

### 2.2 所有后端都是 mock fixtures

retail/travel/telecom/entertainment 的 `MockRetail` / `MockTravel` 等基于 `data/` 假数据；Agent SDK 路径 `load_mock_backend()` 直接加载 mock。生产必须实现真实 `StorefrontBackend` / `MerchantBackend`（见 [`backends.md`](backends.md)）。

### 2.3 MCP server 无认证 + 仅 loopback

`commerce_common/mcp_server.py` 的 `enforce_local_only_bind`（第 26-38 行）拒绝非回环地址，除非设 `..._UNSAFE_ALLOW_NO_AUTH=1`。`main()` 的 warning 自己承认："anyone who reaches it can read carts and orders"。生产必须置于认证网关后，或改用 Managed Agents 的 vault 模型。

### 2.4 模型默认值是本地/演示模型

当前两个 config 的 `model` 都是 `qwen/qwen3.5-9b`——这是本地模型设置，而非参考文档的 `claude-sonnet-5`。生产应按目标平台核对模型 id 语法与可用性（见 [`deployment.md`](deployment.md)：Vertex 带 `@` 日期、Bedrock 两种端点、Foundry 用部署名）。

### 2.5 清单同步靠手工

`system.md`、`agent.yaml` 的工具列表分别由 `prompt` 与 `tools.registry` 生成，`scripts/check.py` 负责比对。应把它设为 CI 门禁：提示/工具字节漂移会破坏跨轮提示缓存前缀。

### 2.6 未提交的硬编码风险（已解决，作为教训保留）

分析过程中曾在 `shopping-agent/runtime-agent-sdk/shopping_agent_sdk/agent.py` 发现把 `ANTHROPIC_BASE_URL` 指向本地 LM Studio 的硬编码。**当前 HEAD 已恢复干净**（`env={"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1"}`）。建议在 CI 加一条检查：源码中不得出现硬编码的 `ANTHROPIC_BASE_URL` / token——这类"本地联调残留混入源码"是 demo→生产最常见的闪爆点。

---

## 3. 模型层依赖的风险

`docs/safety.md:42-59` 说明提示词承载了另一半规则：

- 围栏文本当材料不当指令；
- 条款/数字只从本对话的工具结果陈述；
- 写操作在调用成功后确认；
- 商品按 id 点名、由 UI 补值；
- 专业/医疗/安全问题给"商品 + 转介"。

但这些规则"只在模型遵循指令的范围内成立；表格在任何模型上都成立"。

- **换模型、或关闭 `require_host_approval` 让聊天里打字的"批准"算数**，必须先重跑 safety 这一节的 evals（图谱：`author-commerce-evals` 提供 CI 回放门禁）。
- **跨路径安全不对称**：grounding 在 Messages API 路径用 `tool_choice` 强制；Agent SDK 路径只有 orders/catalog 能宿主侧 prefetch，policy 规则无 prefetch 会失效；Managed Agents 路径完全不强制。选型时不要假设三条路径保护力度相同。

---

## 4. 需要重新设计 / 提升改进的地方（按优先级）

### P0 — 不上线就别上线
1. **状态外置**：会话、购物车、provenance、暂存台账从内存迁到共享存储，支持多 worker 与崩溃恢复；加跨实例写锁。
2. **认证/鉴权网关**：两条 HTTP 路径 + 两个 MCP server 全覆盖；生产 host 从已认证请求推导身份（不是写死的 `demo-user`），身份绝不作为工具参数。
3. **凭据管理**：全部走环境变量 / vault，CI 禁止源码硬编码 endpoint 或 token。

### P1 — 决定正确性与合规
4. **后端真实实现 + 业务规则内聚**：把欺诈/资格/定价/库存规则写进 backend；保留 gates 做 provenance 与 caps 兜底。
5. **支付与审批落地**：宿主实现下单扣款；商家审批 UI + 权限模型（gate 只验证标记，不验证"谁标记的"）。
6. **记忆合规**：个人数据删除入口 + 账户注销联动；DEBUG 日志的保留期与访问控制对齐记忆存储。
7. **模型与平台配置**：核对 `model` / `memory_model` / `analysis_model` 在目标平台存在且 id 语法正确。

### P2 — 质量与可持续
8. **Evals 门禁**：把回放套件接进 CI，换模型/关审批/改提示词时强制跑。
9. **提示缓存稳定性监控**：读 `turn_complete.cache_read_input_tokens`，第二轮非零即报警（前缀漂移）。
10. **跨路径一致性测试**：`tests/test_consumption_paths.py` 已锁提示/工具字节一致，扩展到"安全规则在三路径都生效"的断言。
11. **清单同步门禁**：CI 强制跑 `scripts/check.py`，防止 `system.md` / 工具列表漂移。
12. **全链路可观测性**：结构化日志（会话 id 摘要、工具调用、护栏拒绝原因）、trace、成本与延迟指标——参考实现只有单条 INFO。

---

## 5. 一张图总结

```
参考实现（已做到）              上生产（要做）
──────────────────            ──────────────────
围栏 / provenance / caps  ✓    认证 / 授权        ✗ 部署方补
记忆写入过滤 / 保留期     ✓    速率限制          ✗ 部署方补
宿主审批门控             ✓    业务规则(backend)  ✗ 部署方补
每连接 provenance 记录    ✓    支付              ✗ 部署方补
loopback 绑定            ✓    审批 UI + 权限     ✗ 部署方补
提示词层安全约束         ~      记忆删除/注销联动  ✗ 部署方补
(依赖模型，非硬保证)            DEBUG 日志治理     ✗ 部署方补
                                状态外置/多 worker  ✗ 需重新设计
                                mock → 真实后端    ✗ 需实现
```

`✓` 已内建且跨路径一致；`~` 概率性保证；`✗` 需要部署方补齐或重新设计。

---

## 6. 相关文件索引（来自知识图谱）

- 安全规则清单：`docs/safety.md` / `docs/safety.zh-CN.md`
- 后端对接：`docs/backends.md` / `docs/backends.zh-CN.md`
- 平台部署：`docs/deployment.md` / `docs/deployment.zh-CN.md`
- 共享机制：`commerce_common/execution.py`（executor）、`commerce_common/fencing.py`（围栏）、`commerce_common/memory.py`（记忆/过滤）、`commerce_common/mcp_server.py`（loopback 绑定）
- 会话状态：`examples/demo_common/sessions.py`（`SessionStore`）
- 门控：`shopping_agent/gates.py`、`merchant_agent/gates.py`、`merchant_agent/changes.py`（护栏）
- 一致性测试：`tests/test_consumption_paths.py`、`scripts/check.py`（清单同步）
