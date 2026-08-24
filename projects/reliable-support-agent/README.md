# 综合项目：Reliable Support Agent——用一个系统逐层验证后端基本功

这个项目不是“做一个看起来企业级的架构”。

它的目的只有一个：

> **把已经通过对话/课程理解的后端概念，按最小增量整合到同一个可运行系统里。**

最终可以演进到 PostgreSQL、Redis、Outbox、Agent、Gateway，甚至读懂 K8s；但**起点必须足够简单，让你知道每一层为什么被加入。**

---

## 业务场景

虚构 SaaS 客服系统：

```text
用户
├─ 创建工单
├─ 查看自己的工单
├─ 关闭工单
└─ 发起 Agent 辅助分析任务

外部客服 Provider
└─ Webhook 回传状态/消息
```

只使用虚构数据，不连接真实公司系统。

---

# 核心原则：每个版本都必须单独成立

项目按照：

```text
P0 单服务 + 内存
↓
P1 单服务 + PostgreSQL
↓
P2 Transaction + Auth + Idempotency
↓
P3 Redis + Concurrency（只有解决明确问题才加入）
↓
P4 Outbox + Worker / Streams
↓
P5 Agent / RAG
↓
P6 可选：Gateway / Service Split / K8s
```

不是：

```text
先画最终架构
然后让 AI 一次全部生成
```

每进入下一阶段必须能回答：

1. 上一阶段哪里不够？
2. 新增组件解决什么具体问题？
3. 新增组件自己引入什么故障？
4. 我用什么测试/实验证明？

如果答不出来，先留在当前阶段。

---

# 实现语言怎么选

## 当前想练 Go 后端

P0～P3 可以直接以 Go 为主：

```text
net/http
Handler -> Service -> Repository
context
errors
tests
PostgreSQL
```

不需要等 Python 路线完成。

## 想连接已有 Agent/Python 能力

P5 可以：

- 在同一个 Python Agent Service 中实现；或
- 先用 Python Fake/Provider 实验；或
- 最后再把 Agent 边界拆成独立服务。

项目不要求为了“多语言”同时维护两套完整业务实现。

> **语言是学习工具，业务边界和可靠性才是主目标。**

---

# P0：单服务 + 内存 Repository

第一版故意很简单：

```text
Client
  ↓ HTTP
Ticket API
  ├─ Middleware
  ├─ Handler
  ├─ Service
  └─ InMemory Repository
```

功能只要：

```text
POST /api/v1/tickets
GET  /api/v1/tickets/{id}
GET  /api/v1/tickets
POST /api/v1/tickets/{id}/close
GET  /healthz
```

这一阶段只证明：

- HTTP Method/Path/Header/Body；
- JSON 输入验证；
- Handler/Service/Repository 分工；
- request ID；
- 稳定错误码；
- 状态机基础；
- unit/handler tests。

明确不做：

```text
PostgreSQL
Redis
JWT
Docker
Message Queue
Agent
Gateway
```

### P0 退出条件

关闭 AI 后能：

- 画完整请求链；
- 自己新增一个字段/规则；
- 写对应失败测试；
- 解释进程退出后数据为什么消失。

---

# P1：把业务事实搬到 PostgreSQL

上一阶段的问题：

```text
进程重启
→ 数据消失
```

所以引入：

```text
PostgreSQL
```

架构：

```text
Client
  ↓
API
  ↓
Service
  ↓
Postgres Repository
  ↓
PostgreSQL
```

新增知识：

- migration；
- PK/FK/UNIQUE/CHECK；
- parameterized SQL；
- tenant column；
- index from query shape；
- `EXPLAIN`；
- connection pool；
- statement/request timeout；
- integration tests。

仍然不加 Redis/Queue。

### P1 必须证明

```text
重启 API -> ticket 仍在
非法状态 -> DB constraint 拒绝
tenant A -> 查不到 tenant B
列表查询 -> 索引/EXPLAIN 有依据
```

---

# P2：正确性——Transaction、Authentication、Authorization、Idempotency

有数据库以后，新的真实问题出现：

```text
两个请求同时改怎么办？
客户端 timeout 后重试怎么办？
谁有权改这条 ticket？
```

这一阶段加入：

## Transaction / Version

关闭 Ticket：

```text
expected_version
↓
UPDATE ... WHERE version=?
↓
0 rows -> conflict
```

## Authentication / Principal

可以先继续使用 deterministic test token，重点是：

```text
Credential
↓ server validation
Principal(subject, tenant)
```

不要为了练 JWT crypto 分散主线；JWT 作为独立认证实验即可。

## Authorization

每个资源操作检查：

```text
tenant / owner / permission
```

## Idempotency

创建 Ticket：

```text
Idempotency-Key
+ request hash
+ persistent unique record
```

解决：

```text
COMMIT 成功
HTTP response 丢失
客户端重试
```

### P2 必须证明

- 两个旧 version 更新只有一个成功；
- 相同 Idempotency Key 并发到达只产生一个 Ticket；
- 相同 key 不同 body 被拒绝；
- 未认证 401；
- 无权限 403 或契约定义的隐藏 404；
- client Body 伪造 tenant 无效。

---

# P3：Redis 与 Concurrency——只解决已经看见的问题

这一阶段**不是必然需要 Redis**。

先选一个具体问题。

## 选项 A：Cache

如果要练缓存：

```text
GET ticket
↓
Redis cache
↓ miss
PostgreSQL
```

证明：

- Cache Aside；
- TTL；
- update invalidation；
- Redis 清空后业务事实仍在；
- Redis outage 有有界回源策略。

## 选项 B：Session / Rate Limit

如果要练认证运行时状态：

```text
Session ID -> Redis
```

或：

```text
rate limit counter
```

明确 Redis 角色和故障语义。

## Concurrency

单独练：

- Go worker pool；
- `context` deadline；
- bounded concurrency；
- backpressure；
- retry + jitter；
- `go test -race`。

不要为了“用 Redis”实现一个其实数据库 UNIQUE 就能解决的分布式锁。

### P3 退出条件

能明确说：

```text
这个 Redis key 丢了会怎样？
谁是真实 source of truth？
为什么这里不直接用 PostgreSQL？
```

---

# P4：异步任务、Webhook、Outbox 与 Worker

现在才引入真正异步链。

## Webhook

外部 Provider：

```text
POST webhook
↓
raw-body HMAC
↓
timestamp/replay check
↓
provider event_id unique
↓
transaction
```

证明重复、乱序和签名错误。

## Outbox

业务 transaction：

```text
UPDATE ticket
INSERT outbox event
COMMIT
```

Publisher：

```text
DB outbox
↓
publish
↓
mark published
```

故意模拟：

```text
publish 成功
mark published 前崩溃
```

证明消息可能重复但不会永久丢失。

## Worker

第一版甚至可以：

```text
PostgreSQL job/outbox polling
```

如果已经理解语义，再接 Redis Streams：

```text
XADD
Consumer Group
Pending
ACK
reclaim
```

### P4 必须证明

- Consumer 业务提交后 ACK 前崩溃可恢复；
- 重复 event 不重复业务副作用；
- Pending 可被新 Worker reclaim；
- retry 有上限；
- poison message 可进入 DLQ/人工流程；
- backlog/oldest age 可观测。

---

# P5：Agent / RAG 作为受控后端能力

前面的可靠性边界已经理解以后再引入模型。

Agent Task：

```text
POST /agent-tasks
↓
task=pending
↓
202 task_id

Worker
↓
claim / lease
↓
RAG / Model / Tools
↓
terminal state
```

## 先 Fake，后真实 Provider

第一版：

```text
Deterministic Fake Model
Deterministic Fake Retrieval
```

先证明系统语义：

- task state；
- tenant filter；
- source mapping；
- deadline；
- max steps；
- token/cost budget；
- cancellation；
- failure state。

然后再换真实 Provider。

这样真实模型波动不会把基础后端 bug 混在一起。

## Tool

Tool Registry 至少区分：

```text
read vs side effect
permission
timeout
confirmation
idempotency
audit
```

模型选择 Tool 不代表已授权。

## RAG

必须：

```text
Principal
↓
ACL/tenant filter
↓
retrieval
↓
Model
```

而不是先检索全库再让模型“自觉不泄露”。

### P5 必须证明

- tenant A 永远检索不到 tenant B source；
- no relevant source 时不生成内部事实；
- Agent loop 超过 step/budget 会终止；
- side-effect tool 重试不重复执行；
- SSE 断开不丢 task；
- 任务可以 query/recover terminal state；
- 固定 eval set 可以比较改动前后。

---

# P6：可选高级实验——Gateway、服务拆分、Docker/K8s

这是**可选阶段**。

只有你已经能明确指出网络边界值得存在时再做。

一种拆法：

```text
Client
  ↓
Go Gateway / BFF
  ↓
Ticket/Agent Service
```

这个阶段不是为了证明“会微服务”，而是为了观察拆服务后新增的问题：

- service-to-service authentication；
- deadline propagation；
- error mapping；
- retry amplification；
- trace propagation；
- protocol compatibility；
- graceful shutdown。

如果没有拆分理由，保持 Modular Monolith 完全合格。

## Docker / CI

把已经能独立运行的服务：

```text
build image
↓
CI verify
↓
registry digest
↓
local/target environment
```

## Kubernetes

只要求：

- 读懂 Deployment/Service；
- resources；
- securityContext；
- readiness/liveness；
- migration Job；
- rollout/rollback 思维。

不要求为了项目专门维护生产集群。

---

# 最终能力目标

完成项目不等于“所有 Phase 都打勾”。

真正成功标准是你能拿任何一个阶段解释：

```text
请求怎么走？
身份从哪里来？
事实在哪里？
事务边界在哪里？
并发/重复怎么办？
这里宕机会怎样？
恢复依赖什么？
有什么测试证据？
为什么暂时没有加更复杂组件？
```

如果 P2 你能独立讲得非常扎实，比让 AI 一次生成到 P6 更有价值。

阶段退出条件见 [`phases.md`](phases.md)，能力验收见 [`acceptance.md`](acceptance.md)，架构如何随阶段变化见 [`architecture.md`](architecture.md)。
