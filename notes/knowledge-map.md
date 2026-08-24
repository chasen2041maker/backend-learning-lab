# 后端知识地图：遇到问题先定位层级

这不是名词清单，而是一个排查/学习导航。

当你遇到一个后端问题，不要第一反应搜索框架代码。先问：**问题发生在哪一层？**

```text
用户 / Client
│
├─ 1. 网络与协议
│  ├─ process / IP / port / DNS / TCP / TLS
│  ├─ HTTP method / path / header / body
│  ├─ status code / JSON / REST
│  └─ timeout / connection refused
│
├─ 2. 入口与身份
│  ├─ router / middleware / handler
│  ├─ Cookie / Session / Bearer / JWT
│  ├─ Authentication -> Principal
│  └─ Authorization -> role / owner / tenant
│
├─ 3. 业务规则
│  ├─ Service / use case
│  ├─ state machine
│  ├─ validation / invariants
│  └─ stable domain errors
│
├─ 4. 数据事实
│  ├─ Repository
│  ├─ PostgreSQL / SQL
│  ├─ constraint / index / EXPLAIN
│  ├─ migration / connection pool
│  └─ source of truth / owner
│
├─ 5. 一致性与并发
│  ├─ transaction / COMMIT
│  ├─ optimistic/pessimistic lock
│  ├─ race / version
│  ├─ idempotency
│  └─ retry / deadlock / isolation
│
├─ 6. 运行时加速与协调
│  ├─ Redis role
│  ├─ cache / TTL / invalidation
│  ├─ rate limit / session
│  └─ lease / coordination / fencing
│
├─ 7. 并发执行与资源边界
│  ├─ goroutine / channel / mutex
│  ├─ async/await / event loop
│  ├─ worker pool / semaphore
│  ├─ deadline / cancel
│  └─ backpressure / bounded concurrency
│
├─ 8. 异步与消息
│  ├─ job / command / event
│  ├─ Outbox
│  ├─ Stream / consumer group
│  ├─ Pending / ACK / reclaim
│  └─ duplicate / ordering / DLQ
│
├─ 9. 安全
│  ├─ password hashing / Secret / HTTPS
│  ├─ SQL injection / mass assignment / SSRF
│  ├─ XSS / CSRF / CORS
│  ├─ least privilege
│  └─ audit / sensitive-data logging
│
├─ 10. 证明与排错
│  ├─ unit / integration / contract / E2E
│  ├─ regression / fault test
│  ├─ log / request ID
│  ├─ metric / RED
│  └─ trace / SLO / alert
│
├─ 11. 交付与运行
│  ├─ Git / CI pipeline
│  ├─ Image / Container / Registry
│  ├─ Compose / Volume / Network
│  ├─ deployment / migration / rollback
│  └─ Kubernetes / probe / resources
│
├─ 12. 服务边界
│  ├─ modular monolith
│  ├─ reverse proxy / load balancer
│  ├─ API Gateway / BFF
│  ├─ REST / gRPC / SSE / event
│  └─ microservice / service identity
│
└─ 13. Agent / RAG
   ├─ retrieval permission / source
   ├─ workflow / agent loop
   ├─ tool schema + authorization
   ├─ model/tool deadline + budget
   ├─ task state / idempotency / audit
   └─ offline eval / online metrics
```

## 一条最重要的因果链

很多后端知识可以这样串起来：

```text
一次 HTTP 请求
↓
要知道是谁 -> Authentication
↓
要知道能不能做 -> Authorization
↓
要改变事实 -> Database
↓
多个事实一起改 -> Transaction
↓
两个请求一起改 -> Lock / Version
↓
客户端可能重试 -> Idempotency
↓
读取太慢且允许 stale -> Cache
↓
后台工作太慢 -> Async Worker
↓
DB + Broker 双写 -> Outbox
↓
消息可能重复 -> Consumer Idempotency
↓
组件越来越多 -> Logs / Metrics / Traces
↓
要稳定交付 -> CI / Image / Deployment
↓
真的需要独立边界 -> Service split / Gateway
```

这个顺序不是绝对课程顺序，但它说明很多“高级组件”其实是前一层问题推导出来的。

## 当你看到一个新技术时，用五问定位

例如有人说：

```text
我们需要 Kafka
```

先问：

1. 它在哪一层？
2. 现在什么具体问题没有它解决不了？
3. 当前规模/失败模式有证据吗？
4. 它会增加什么状态、依赖和运维成本？
5. 用更简单的 PostgreSQL / Worker / Redis Streams 是否已经足够？

对 Redis、K8s、微服务、向量数据库同样适用。

## Agent/RAG 不在普通后端之外

Agent 只是额外加入：

```text
模型非确定性
Token / Cost
Tool 权限
Prompt injection
RAG source / eval
```

它仍然需要前面所有基础：

```text
HTTP
身份
事务
幂等
并发
timeout
日志
测试
部署
```

尤其牢记：

> 模型选择了 Tool，不代表 Tool 获得权限；模型输出也不是高风险事实或授权决定。

完整依赖导航见 [`LEARNING_ROADMAP.md`](../LEARNING_ROADMAP.md)。
