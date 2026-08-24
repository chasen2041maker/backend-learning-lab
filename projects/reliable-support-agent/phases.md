# 综合项目分阶段交付：一次只增加一个主要复杂度

这些 Phase 不是时间计划，也没有“几周必须完成”。

每个阶段都要：

```text
能单独运行
能单独测试
能说明新增复杂度
能制造至少一个代表性失败
能解释当前仍然没有解决什么
```

满足退出条件以后再进入下一阶段。

---

# P0：单服务内存 API

## 目标

只建立最小后端请求心智模型。

```text
Client
→ HTTP Server
→ Middleware
→ Handler
→ Service
→ InMemory Repository
```

## 只做

- `GET /healthz`；
- create/get/list/close Ticket；
- strict input；
- stable error code；
- request ID；
- Ticket state machine；
- unit/handler tests。

## 不做

- PostgreSQL；
- Redis；
- JWT 实现；
- Docker；
- Outbox；
- Agent；
- Gateway。

## 必须制造的失败

- wrong Method -> 405；
- invalid JSON / invalid field；
- unknown Ticket；
- invalid state transition；
- 进程重启 -> 内存事实丢失。

## 退出条件

关闭答案可以：

- 画一次 Request -> Response；
- 自己新增一个字段并改正确层；
- 写对应测试；
- 解释内存 Repository 为什么不是持久化。

建议快照：

```text
capstone-p0-memory
```

Tag 是学习证据，不是生产 release。

---

# P1：PostgreSQL 事实源

## 为什么进入

P0 最大限制：

```text
Process restart -> data lost
```

## 新增

```text
Repository implementation
→ PostgreSQL
```

学习：

- migration；
- schema/constraint；
- parameterized SQL；
- tenant column；
- query/index；
- EXPLAIN；
- cursor pagination；
- connection pool；
- DB timeout；
- integration tests。

## 不做

仍然不需要：

```text
Redis
Queue
Microservice split
```

## 必须制造的失败

- constraint violation；
- database unavailable；
- statement timeout；
- duplicate unique value；
- tenant A 尝试读取 tenant B 数据。

## 退出条件

能证明：

```text
API restart -> data remains
invalid fact -> database refuses
tenant query -> scoped in SQL
index -> has EXPLAIN evidence
```

建议快照：

```text
capstone-p1-postgres
```

---

# P2：Transaction + Auth + Idempotency

## 为什么进入

P1 有了持久事实，但还没有解决：

```text
并发写
重复请求
身份/权限
提交后响应丢失
```

## 新增

### Transaction / version

- 乐观版本；
- 明确 transaction boundary；
- unique constraint；
- deadlock/冲突错误分类。

### Trusted Principal

- deterministic credential/test token；
- Middleware 产生 `Principal(subject, tenant)`；
- Body 中 tenant/user 不可信。

### Authorization

- tenant；
- owner；
- permission / role（只加必要规则）。

### Idempotency

- `Idempotency-Key`；
- persistent unique record；
- request hash；
- replay previous result。

## 必须制造的失败

### F1：并发旧版本

```text
A read version=1
B read version=1
A update success -> v2
B update with v1 -> conflict
```

### F2：COMMIT 后 Response 前失败

```text
DB commit ✅
return 前抛错
client retry
```

最终只能存在一个业务资源。

### F3：相同 key 不同 body

必须稳定拒绝，而不是静默返回旧结果。

### F4：伪造 tenant

Body 改 tenant 不得改变服务端 Principal。

## 退出条件

能独立解释：

```text
401 vs 403 vs hidden 404
transaction protects what
idempotency protects what
optimistic conflict
```

建议快照：

```text
capstone-p2-correctness
```

---

# P3：Concurrency + Redis（按需要选）

## 为什么进入

这一阶段不是“项目必须有 Redis”。

先选择一个具体学习目标。

## Track A：Go/Python Concurrency

- worker pool；
- channel/mutex；
- `context` / cancel；
- bounded concurrency；
- downstream timeout；
- retry/backoff/jitter；
- race test。

## Track B：Redis Cache

如果要学习缓存：

```text
PostgreSQL = source of truth
Redis = derived cache
```

验证：

- miss/hit；
- TTL；
- invalidation；
- Redis flush 后可恢复；
- outage 时有界回源。

## Track C：Session / Rate Limit

如果选择：

```text
Session -> Redis
```

需要明确：

```text
Redis 丢失 -> 用户会话失效
但业务事实不丢
```

如果选择 rate limit，明确 fail-open/fail-closed policy。

## 不做

不要为了这一阶段：

```text
随便加 Redis distributed lock
```

先证明 database UNIQUE/version/transaction 不够。

## 退出条件

至少一个 Track 达到 L3，并能回答：

```text
这个运行时状态为什么放 Redis？
它丢了会怎样？
并发上限由什么决定？
```

建议快照：

```text
capstone-p3-runtime
```

---

# P4：Webhook + Async + Outbox

## 为什么进入

出现：

```text
外部事件重试
后台工作
数据库事实必须可靠触发事件
```

## Webhook

实现：

```text
raw bytes
→ timestamp/replay window
→ HMAC
→ provider event_id dedupe
→ entity version/sequence
→ transaction
```

## Outbox

同一 DB transaction：

```text
business change
+ outbox row
```

Publisher 负责外发。

## Worker / Transport

优先先把消息语义证明清楚。

可以：

```text
DB polling worker
```

再升级到：

```text
Redis Streams
Consumer Group
Pending
ACK
reclaim
```

## 必须制造的失败

- duplicate webhook；
- stale/out-of-order webhook；
- bad HMAC；
- publish 成功但 mark published 前崩溃；
- Consumer COMMIT 后 ACK 前崩溃；
- Worker 持有 lease 后失联；
- poison message 多次失败。

## 退出条件

能画：

```text
DB transaction
→ Outbox
→ Publisher
→ Transport
→ Consumer
→ DB
→ ACK
```

并在每条箭头处说明：

```text
这里失败会怎样？
```

建议快照：

```text
capstone-p4-async
```

---

# P5：受控 Agent / RAG

## 为什么进入

前面普通后端语义已足够稳定，现在引入一个：

```text
不确定 + 慢 + 贵 + 可能调用 Tool
```

的依赖。

## 先用 Fake

第一版必须 deterministic：

```text
Fake Retrieval
Fake Model
Fake Tool
```

先验证系统控制流，而不是模型表现。

## Agent Task

状态：

```text
pending
running
succeeded
failed
cancelled
```

支持：

- task query；
- cancellation；
- lease/fencing；
- retry policy；
- SSE observe/reconnect。

## RAG

```text
Principal
→ tenant/ACL filter
→ retrieval
→ source mapping
→ model
```

## Tool

执行前：

```text
schema
permission
tenant/owner
confirmation
idempotency
timeout
audit
```

## Budget

至少有限制：

```text
max steps
max tool calls
wall-clock deadline
input/output token
retrieved docs/result bytes
```

## Eval

建立固定样本：

- expected facts/source；
- no-source case；
- tenant isolation；
- tool auth；
- latency/token/cost。

## 必须制造的失败

- Retrieval 返回 0 source；
- Model timeout；
- Tool timeout；
- unauthorized Tool；
- side-effect Tool timeout after success；
- Agent loop 超预算；
- Worker lease 被接管；
- SSE 断线。

## 退出条件

能解释：

> 模型输出为什么不是权限决定？Tool 为什么仍然是普通后端副作用？

建议快照：

```text
capstone-p5-agent
```

---

# P6：可选 Gateway / Service Split / Deployment

## 这阶段可以不做

如果单服务已经能完整展示后端能力，完全可以在 P5 停止。

只有想专门练网络边界/部署时进入。

## Option A：Gateway / BFF

把原来进程内边界拆成网络：

```text
Client
→ Go Gateway
→ Owner Service
```

新增验证：

- service identity；
- Principal propagation；
- deadline propagation；
- stable error mapping；
- network partial failure；
- trace propagation；
- retry owner。

如果只是启动两个端口但解释不了这些，就没有学到“拆服务”的核心。

## Option B：Docker / CI

- multi-stage image；
- non-root；
- digest；
- CI format/lint/test/build；
- Compose；
- graceful shutdown。

## Option C：K8s 阅读能力

- Deployment；
- Service；
- resources；
- readiness/liveness；
- migration Job；
- rolling update；
- rollback compatibility。

不要求真实生产集群。

## 退出条件

能回答：

```text
为什么这个边界值得从模块变成网络？
部署后新增的最大失败是什么？
如果删掉 K8s/Gateway，业务语义是否仍然清楚？
```

建议快照：

```text
capstone-p6-boundaries
```

---

# Phase 规则

## 1. 不按时间推进

一阶段两天或两个月都可以。

## 2. 不要求每个阶段用两种语言

用当前真正学习/工作的语言证明概念。

## 3. 新组件必须有前一阶段痛点

提交说明里可以写：

```text
Why introduced:
Failure it addresses:
New failure modes:
Evidence:
```

## 4. 不能只有 Happy Path

每阶段至少有代表性故障实验。

## 5. Tag 不代表“生产发布”

它只是：

```text
这个能力阶段有一份可复现快照
```

## 6. AI 不能一次生成下一阶段所有代码

可以让 AI：

- 解释；
- review；
- 给失败测试；
- 给完整 reference（明确要求时）；

但真正验收仍然要求自己能复述和修改。
