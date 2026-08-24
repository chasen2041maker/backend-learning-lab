# 学习进度：按“能力证据”记录，不按读到第几章打勾

> 当前真正应该从哪里继续，请先看 [`current-focus.md`](current-focus.md)。本文件负责长期能力证据；`current-focus.md` 负责新 AI 会话的短期接棒。

不要用：

```text
第 7 课看完了
```

代表掌握。

这里记录的是：

> **关闭答案以后，我现在能独立做到什么？有什么证据？**

---

## 掌握等级

每个能力可以标一个等级：

```text
L0 未接触
L1 见过：知道名词和大概作用
L2 能解释：能画数据流、说明为什么和失败点
L3 能独立：能实现、测试、排错
L4 能权衡：知道什么时候不用它、替代方案和成本
```

仓库的基础主干至少争取 L2；经常使用的能力逐渐达到 L3；系统设计/选型逐渐达到 L4。

不要为了好看全部填高。

---

# 1. HTTP、进程与请求生命周期

当前等级：`L_`

我是否能独立解释：

- 源代码、进程、IP、端口分别是什么；
- request 如何从网络到 Router/Middleware/Handler；
- 400、401、403、404、405、422、500 的层级差异；
- `connection refused` 为什么甚至还没到 Handler；
- Request ID 在哪里生成和传播。

能力证据：

```text
日期：
我亲手运行的服务：
我制造的失败：
测试/命令：
我仍然讲不清：
```

---

# 2. Handler / Service / Repository

当前等级：`L_`

我是否能：

- 看一个需求判断应该改哪一层；
- 解释为什么 Handler 不应该直接塞满 SQL；
- 解释 Service 和“HTTP Handler helper”有什么区别；
- 用 interface/Protocol 隔离数据访问；
- 替换 in-memory Repository 而不重写业务规则。

证据：

```text
功能：
自己修改过的文件：
测试：
一次分层错误以及如何修正：
```

---

# 3. API Contract 与可信输入

当前等级：`L_`

我是否能：

- 区分 JSON 语法错误和字段/业务验证错误；
- 定义稳定 machine-readable error code；
- 解释为什么 client `tenant_id/user_id/role` 不可信；
- 说明兼容性变化和 breaking change；
- 让 Python/Go 读取同一机器契约。

证据：

```text
契约 case：
制造过的 contract drift：
失败结果：
修复后的验证：
```

---

# 4. SQL / PostgreSQL

当前等级：`L_`

我是否能：

- 写基本 SELECT/INSERT/UPDATE/DELETE；
- 使用参数化 SQL；
- 根据业务不变量设计 PK/FK/UNIQUE/CHECK；
- 根据真实查询设计索引；
- 用 EXPLAIN 解释计划，而不是只说“建索引更快”；
- 识别 N+1；
- 解释 connection pool / statement timeout / migration；
- 保证 tenant/owner 条件进入 SQL。

证据：

```text
Schema：
真实查询：
索引：
EXPLAIN 前后：
一次 constraint 失败：
```

---

# 5. Transaction / Lock / Idempotency

当前等级：`L_`

我是否能：

- 解释 COMMIT 和客户端收到响应为什么是两个时刻；
- 画出 COMMIT 前、COMMIT 后响应前两个宕机窗口；
- 解释 lost update；
- 实现/解释 optimistic version check；
- 说明 `FOR UPDATE` 的代价；
- 理解 deadlock 和有限重试；
- 使用 UNIQUE/transaction 解决并发唯一性；
- 设计 Idempotency Key + request hash；
- 解释 transaction 为什么不能 rollback 外部 HTTP/邮件。

证据：

```text
我做过的失败实验：
重复请求结果：
并发冲突结果：
相关测试：
```

---

# 6. Redis

当前等级：`L_`

每次看到 Redis，我是否先能说明角色：

```text
cache / session / rate-limit / coordination / stream
```

我是否能：

- 解释 Cache Aside；
- 说明 TTL 不是一致性保证；
- 区分穿透/击穿/雪崩；
- 解释为什么 cache 丢失应该可重建；
- 使用原子命令避免 read-modify-write race；
- 分析 Redis unavailable 时 fail-open/fail-closed/degrade；
- 解释 `SET NX PX` 为什么不是完整锁语义；
- 理解 lease/fencing。

证据：

```text
Redis 角色：
清空 Redis 后发生什么：
我制造过的缓存/锁失败：
```

---

# 7. Go / Python 并发、Timeout 与 Cancel

当前等级：`L_`

我是否能：

- 区分 concurrency / parallelism；
- 解释 goroutine 不是 OS thread 的简单别名；
- 写有界 worker pool；
- 区分 channel / mutex 适用场景；
- 使用 `go test -race`；
- 解释 Python event loop / `await`；
- 识别 async 函数中的 blocking call；
- 传播 context/deadline/cancel；
- 实现 bounded concurrency/backpressure；
- 设计有限 retry + backoff + jitter + total budget。

证据：

```text
并发实验：
最大并发：
timeout 实验：
race detector 结果：
```

---

# 8. Async / Outbox / Streams

当前等级：`L_`

我是否能：

- 解释为什么某个工作需要异步，而不是因为“队列高级”；
- 区分 command/event/job；
- 解释 at-least-once 和 consumer idempotency；
- 画出 ACK 太早和 ACK 太晚的失败窗口；
- 解释 DB + Broker dual write；
- 说明 Outbox 保证什么、不保证什么；
- 解释 Publisher 为什么仍可能重复发布；
- 理解 Consumer Group / Pending / reclaim；
- 解释 lease/fencing / stale worker；
- 设计 retry/DLQ 和 backlog metrics。

证据：

```text
我模拟过的 crash 点：
Pending/reclaim 结果：
重复 event 结果：
```

---

# 9. Authentication / Authorization / Security

当前等级：`L_`

我是否能不看文档解释：

```text
Cookie
Session
Token
Bearer
JWT
Access Token
Refresh Token
```

并且能：

- 区分 Authentication / Authorization；
- 解释可信 Principal；
- 设计 owner/tenant 服务端检查；
- 理解 401/403/跨租户 404；
- 说明 password hashing 和普通 SHA-256 的区别；
- 解释 XSS/CSRF/CORS；
- 说明 JWT logout/revoke 的现实问题；
- 不把前端按钮/Prompt 当权限边界。

证据：

```text
权限测试：
跨租户测试：
我能独立画的登录链：
仍然模糊的安全主题：
```

---

# 10. Testing / Debugging

当前等级：`L_`

我是否能：

- 区分 unit/integration/contract/E2E/fault test；
- 先写复现 bug 的 regression test；
- 识别 flaky test；
- 判断 mock 是否隐藏真实风险；
- 用预期/实际/复现/假设/最小实验调试；
- 找“第一个错误状态”；
- 给 code review issue 写出触发场景、最小修复和验证。

证据：

```text
最近一个真实 bug：
失败测试：
根因：
回归测试：
```

详细记录放 [`debug-log.md`](debug-log.md)。

---

# 11. Observability

当前等级：`L_`

我是否能：

- 区分 log/metric/trace；
- 正确使用 request ID/trace ID；
- 设计 HTTP RED；
- 识别 high-cardinality metric label；
- 为 async Worker 设计 backlog/oldest age；
- 区分 liveness/readiness；
- 解释 SLI/SLO/SLA/error budget；
- 写一个有行动性的 Alert，而不是任何异常都报警。

证据：

```text
Dashboard/metrics：
一次排障链：
Alert：
```

---

# 12. Docker / CI / Kubernetes

当前等级：`L_`

我是否能：

- 区分 Image/Container/Volume；
- 解释 Container 和 VM；
- 说明容器里的 `localhost`；
- 解释 Registry/Tag/Digest；
- 读懂基础 Dockerfile/Compose；
- 解释 CI/pipeline/CD；
- 说明为什么构建 artifact 后再部署；
- 区分 Pod/Deployment/Service；
- 解释 desired state/reconciliation；
- 理解 readiness/liveness 对 rollout 的影响；
- 说明 K8s 不会替应用解决 migration/兼容性。

证据：

```text
我 build/run 的 Image：
CI run：
K8s dry-run：
我仍不会的部署问题：
```

---

# 13. 服务边界与系统设计

当前等级：`L_`

我是否能：

- 区分 modular monolith / microservice；
- 从真实 owner/部署/扩缩需求判断是否拆服务；
- 区分 reverse proxy/LB/Gateway/BFF；
- 选择同步 REST/gRPC vs async event；
- 解释 service-to-service auth/deadline；
- 从需求 -> 容量 -> 数据模型 -> 正常流 -> 失败窗口推导架构；
- 解释为什么暂时不用 Redis/Kafka/K8s/sharding；
- 给一个组件写出 trade-off。

证据：

```text
我设计过的系统：
容量估算：
最大失败窗口：
一个我主动没有引入的组件及理由：
```

---

# 14. RAG / Agent 工程化

当前等级：`L_`

我是否能：

- 区分 Workflow / Agent / Tool Calling；
- 解释 Tool Call 只是模型输出，不是权限；
- 在 retrieval 前执行 tenant/ACL filtering；
- 把 vector index 当派生数据管理；
- 给模型/tool 设置 deadline/token/step/cost budget；
- 为 side-effect tool 做 authorization/confirmation/idempotency/audit；
- 把 Agent Task 当持久化状态机；
- 区分 retrieval/eval/model/tool 根因；
- 维护固定 eval set 和 online metrics。

证据：

```text
Agent/RAG 设计：
权限实验：
Bad Case 根因：
预算限制：
```

---

# 本周/当前学习焦点（可随时改）

这里不要维护第二份“当前进度”。真正的会话接棒点统一写在 [`current-focus.md`](current-focus.md)。

本文件只在已经产生能力证据时更新等级和证据。

---

# 一次学习结束后的最短记录

如果不想填写整页，只写：

```text
日期：
主题：
以前我以为：
现在我理解：
我亲手验证：
一个失败场景：
当前等级：L_
下一步：
```

这个进度表的目标不是制造打卡压力，而是让未来的自己清楚：**哪些只是“听过”，哪些已经成为可以独立使用的能力。**
