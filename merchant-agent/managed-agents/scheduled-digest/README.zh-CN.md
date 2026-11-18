# scheduled-digest

`run_morning_digest.py` 在无操作者的情况下运行 digest：一次 `MerchantAgent` 回合（`merchant_agent_runtime`，即 Messages API runtime）跑在 retail 示例的 mock merchant 之上，询问"今天有什么需要关注"。它打印回复和 `present_digest` payload；`--out FILE` 还会把整个结果（提示词、文本、digest、其他组件）以 JSON 写入文件。环境变量 `MERCHANT_ID`（默认 `acme-retail`）、`MERCHANT_OPERATOR`（默认 `scheduled-digest`）和 `MERCHANT_TIMEZONE`（未设置：以机器本地日期为今天）决定它运行时的会话；`build_demo_agent` 是那个要替换成基于你自己的 `MerchantBackend` 的 `MerchantAgent` 的函数。

```bash
python merchant-agent/managed-agents/scheduled-digest/run_morning_digest.py --out digest.json
```

凭据：runtime 的默认客户端读取 `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN`。退出码 2 表示没有凭据可用，1 表示其他任何失败。

- 从任意任务运行器（job runner）在商店的晨间时间运行它，凭据由运行器的 secret store 提供。
- 把 `--out` 文件保留为作业产物，让退出码驱动重试。它构造的 config 保持 `require_host_approval` 开启，且会话初始没有任何批准，所以重复运行可以暂存变更，但绝不会应用变更。
- 把 `digest` 字段投递给系统、文本投递给人；某条目在本回合中被工具返回过 `ref_id`，它就携带对应的 listing 或变更记录（`enrich_digest`）。

测试：`merchant-agent/runtime-messages-api/tests/test_scheduled_digest.py` 用 `commerce_common.testing.FakeClient` 运行 `run_digest`。
