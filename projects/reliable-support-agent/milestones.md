# 综合项目能力里程碑：不是功能清单，而是“我已经能独立证明什么”

`phases.md` 描述系统怎么演进；这份文件只记录**能力里程碑**，避免和 Phase 重复成两套项目计划。

不要求按编号严格完成，也不要求一次全部达到。

---

## M1：我能独立解释一次 HTTP 请求

证据：

- 能画 Client -> Middleware -> Handler -> Service -> Repository；
- 能区分 network failure 和 HTTP error；
- 能自己新增一个 API 规则和测试；
- 能解释 request ID。

对应阶段：P0。

---

## M2：我能把业务事实交给数据库保护

证据：

- 能写 migration；
- 能用 PK/FK/UNIQUE/CHECK 表达不变量；
- 使用 parameterized SQL；
- tenant 条件进入真实查询；
- 能从 query shape 设计 index 并读 `EXPLAIN`；
- 能解释 connection pool/timeout。

对应阶段：P1。

---

## M3：我能推演并发、重复和提交失败窗口

证据：

- 能画 COMMIT 后 Response 前崩溃；
- Idempotency Key 重试不会重复创建；
- 两个旧 version 更新只有一个成功；
- 能解释 transaction 不能 rollback 外部副作用；
- 能说明什么时候用 UNIQUE、version、`FOR UPDATE`。

对应阶段：P2。

---

## M4：我能守住身份和租户边界

证据：

- Credential -> server validation -> Principal；
- 不相信 Body `user_id/tenant_id/role`；
- 未登录、无权限、跨租户测试齐全；
- 能区分 Authentication / Authorization / owner / tenant；
- 能解释 Session/JWT 取舍而不是只会生成 Token。

对应阶段：P2，可结合第 10 课单独深化。

---

## M5：我能控制并发和运行时资源

证据：

- Go worker pool 或 Python async 有明确并发上限；
- downstream 有 deadline；
- cancellation 能传播；
- retry 只针对可重试错误并带 budget/backoff/jitter；
- 能解释 data race vs business race；
- 如果使用 Redis，能明确它的角色和丢失后果。

对应阶段：P3。

---

## M6：我能设计可恢复的异步链

证据：

- duplicate Webhook 不重复应用；
- 能解释 DB + Broker dual write；
- Outbox Publisher 崩溃后能恢复；
- Consumer COMMIT 后 ACK 前崩溃可重投但不重复副作用；
- Pending/reclaim 可观察；
- retry/DLQ 有边界；
- lease/fencing 防 stale Worker。

对应阶段：P4。

---

## M7：我能把 Agent 当受控后端依赖

证据：

- Retrieval 在模型看到数据前做 ACL/tenant filter；
- Tool Call 不等于授权；
- Side-effect Tool 有确认/幂等/审计；
- Agent 有 step/time/token/cost budget；
- Task state 可恢复；
- no-source / timeout / unauthorized tool 都有稳定终态；
- 有固定 Eval Set，并能按根因分类 Bad Case。

对应阶段：P5。

---

## M8：我能用证据调试和观察系统

证据：

- 一个真实 bug 有稳定复现 -> 假设 -> 最小实验 -> regression test；
- 能区分 unit/integration/contract/E2E/fault test；
- HTTP 有 RED；
- async 有 backlog/oldest age；
- logs 有 request/trace/event/task 关联；
- 能区分 liveness/readiness；
- 一条 Alert 有阈值、持续时间和行动方案。

可以贯穿所有阶段，不等最后才做。

---

## M9：我能解释部署链，而不只是会 Docker 命令

证据：

```text
git commit
-> CI
-> tested artifact/image
-> registry digest
-> deployment
-> readiness
-> rollout/rollback
```

并能：

- 区分 Image/Container/Volume；
- 解释 Container `localhost`；
- 读懂基础 Dockerfile/Compose；
- 读懂基础 Deployment/Service/Probe；
- 解释 migration 为什么影响 rollback。

对应阶段：P6 可选。

---

## M10：我能做取舍，而不是堆组件

这是最高价值的里程碑。

给任何组件：

```text
Redis
Kafka
K8s
Microservice
Vector DB
Gateway
```

都能回答：

1. 它解决当前哪一个真实问题？
2. 不用它会发生什么？
3. 新增什么失败和运维成本？
4. 当前规模有证据需要吗？
5. 更简单方案为什么不够？

如果能稳定做到这一点，说明学习已经从“会用工具”进入“能做后端工程判断”。

---

## 怎么记录

不要在这里做大量 checkbox。

把当前能力等级和证据写在根目录 [`progress/README.md`](../../progress/README.md)。

真正代表某个项目阶段的代码快照，用 `phases.md` 建议的 Git Tag 保存即可。
