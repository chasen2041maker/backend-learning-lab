# 第 14 课：单体、网关、微服务、REST、gRPC 与事件——服务边界应该从哪里拆

后端架构里最容易被“高级名词”带跑的一组概念：

```text
monolith
microservice
reverse proxy
load balancer
API gateway
BFF
REST
gRPC
message/event
```

最常见错误不是“不会这些技术”，而是：

> **还没出现需要拆分的问题，就先因为架构图好看把一个简单系统拆成很多服务。**

本课的核心原则：

> 先把业务边界和事实 owner 做清楚，再决定是否需要网络边界。

---

# 1. 先从一个单进程开始

最小后端：

```text
Client
  ↓
API Process
  ├─ ticket module
  ├─ user module
  └─ agent module
       ↓
   PostgreSQL
```

这通常被叫：

```text
Monolith
```

但“单体”并不等于：

```text
所有代码都写 main.go
所有表随便互相改
没有模块
```

一个单体完全可以有清楚模块边界。

---

# 2. Modular Monolith 为什么值得先学

模块化单体：

```text
一个部署单元
但内部边界清楚
```

例如：

```text
Ticket module
  owns tickets

Identity module
  owns users/sessions

Agent module
  owns tasks
```

模块之间通过明确接口调用，而不是随便越层访问内部数据。

好处：

- 本地调试简单；
- transaction 容易；
- 部署简单；
- 网络失败少；
- 仍然可以练 owner/boundary。

所以：

> 模块边界应该先于微服务边界。

---

# 3. 为什么拆成微服务会增加很多新问题

单体内部函数调用：

```text
TicketService -> UserService method
```

拆开：

```text
Ticket Service
      |
      | network
      v
User Service
```

马上新增：

```text
DNS / service discovery
network timeout
serialization
authentication between services
retry
version compatibility
partial failure
observability
independent deployment
```

原来一个函数错误，变成一个分布式系统问题。

所以微服务不是“更成熟的分层”。

它是一种用更多运行时复杂度换取某些组织/扩展能力的架构选择。

---

# 4. 什么情况可能值得拆服务

常见真实驱动力：

- 不同模块需要真正独立发布；
- 不同团队需要明确 ownership；
- 某一模块扩缩容特征极不一样；
- 安全/合规隔离要求；
- 技术栈/运行环境差异明显；
- 单体已经因为边界混乱而无法独立演进，并且模块化重构仍不足。

不够好的理由：

```text
大厂都用
简历更好看
以后可能高并发
我想练 gRPC
```

练技术可以做实验，但不要把实验误当成必要架构。

---

# 5. Owner Service / Fact Owner 是什么

假设：

```text
Ticket Service owns tickets table
```

意思：

> ticket 的业务事实由这个边界负责修改。

其他服务不应该：

```text
直接 UPDATE tickets
```

即使它们技术上能连同一个 PostgreSQL。

正确方向：

```text
Other Service
   ↓ API / command / event
Ticket owner
   ↓
update facts
```

为什么？

否则：

```text
Ticket Service 以为只有自己的状态机能关闭 ticket
另一个服务直接 UPDATE status
→ 业务不变量被绕过
```

---

# 6. “一个数据库”不等于“可以共享所有表”

早期系统完全可以：

```text
多个模块
共用一个 PostgreSQL instance
```

但逻辑 ownership 仍然应该清楚。

例如：

```text
schema/table ownership
repository ownership
write path ownership
```

微服务不要求“一服务一个物理数据库服务器”；真正关键是写入边界。

当然如果两个服务可以任意读写对方表，那它们实际上仍然强耦合。

---

# 7. REST 是什么层面的选择

REST 通常指基于 HTTP、围绕资源和标准语义设计 API 的架构风格。

现实中很多人说“REST API”主要是指：

```text
HTTP + JSON + resource-oriented endpoints
```

例如：

```http
POST /api/v1/tickets
GET /api/v1/tickets/{id}
PATCH /api/v1/tickets/{id}
```

优点：

- 浏览器/curl 友好；
- 生态广；
- 外部 API 易接入；
- HTTP semantics 熟悉。

问题：

- schema 通常需要额外 OpenAPI/契约维护；
- JSON 开销；
- 同步网络依赖；
- 客户端/服务端兼容仍然需要设计。

---

# 8. gRPC 是什么

gRPC 常基于 HTTP/2 + Protocol Buffers 提供 RPC 框架。

调用代码可能像：

```text
client.GetTicket(request)
```

但背后仍然是网络调用。

最重要的心智模型：

> 看起来像本地函数，不代表它拥有本地函数的可靠性和延迟。

它仍可能：

- timeout；
- connection reset；
- 服务不存在；
- 对端已经执行但响应丢失；
- 版本不兼容。

---

# 9. 为什么内部服务常考虑 gRPC

可能优势：

- 强类型 schema；
- 代码生成；
- 二进制序列化；
- streaming RPC；
- 多语言协议明确。

但代价：

- `.proto` 演进规则；
- 生成代码；
- 调试门槛；
- gateway/browser 适配；
- 仍需 deadline/retry/observability。

所以不是：

```text
内部服务 = 必须 gRPC
```

HTTP/JSON 在很多内部系统完全够用。

---

# 10. Protobuf 为什么强调字段编号

例如：

```proto
message Ticket {
  string id = 1;
  string title = 2;
}
```

线协议主要依赖 field number。

如果以后删除字段 2，不能随便把 2 重新用于完全不同语义。

一般要：

```proto
reserved 2;
reserved "title";
```

新增字段使用新编号。

这就是 schema evolution。

---

# 11. HTTP / gRPC 都是同步调用吗

它们都可以支持不同模式，但最常见 unary 调用是：

```text
Caller 发请求
等待 Callee 返回
```

因此调用方生命周期直接依赖下游。

例如：

```text
Gateway
→ Service A
→ Service B
→ Model Provider
```

每加一跳：

- latency 增加；
- timeout 配置增加；
- 故障概率增加；
- capacity coupling 增加。

这就是同步调用链不能无限拉长的原因。

---

# 12. Event 是另一种通信语义

事件表达：

> 一个事实已经发生。

例如：

```text
ticket.closed
```

Ticket owner 发布事实。

其他消费者：

```text
Notification
Analytics
Search projection
```

各自处理。

Ticket Service 不必同步等待所有消费者。

---

# 13. Event 和 Command 不要混淆

Command：

```text
请做某件事
```

例如：

```text
CloseTicket
SendEmail
```

Event：

```text
某件事已经发生
```

例如：

```text
TicketClosed
EmailSent
```

命名只是一个信号，真正要看语义。

不要发一个叫：

```text
TicketClosedEvent
```

但实际上要求消费者“帮我决定要不要关闭 Ticket”。

---

# 14. 什么时候适合同步，什么时候适合异步

## 同步更自然

调用方必须马上知道结果才能继续：

```text
查询 ticket
验证权限
创建业务资源并立即返回 ID
```

## 异步更自然

后续处理可以延迟：

```text
发通知
更新 analytics
生成长报告
慢 Agent Task
```

核心问题：

> Caller 是否必须在当前请求内得到这个工作的最终结果？

---

# 15. 不要用事件模拟所有 RPC

如果客户端问：

```text
这个 ticket 当前标题是什么？
```

你却：

```text
发布 query.requested event
等 reply event
```

通常会把简单查询变成复杂协议。

异步不是“比 HTTP 解耦，所以什么都用 event”。

选择要匹配业务语义。

---

# 16. Reverse Proxy 是什么

Reverse Proxy 位于客户端和后端服务器之间：

```text
Client
  ↓
Reverse Proxy
  ↓
Backend
```

它代表后端接收流量。

常见能力：

- TLS termination；
- routing；
- header handling；
- compression；
- basic load balancing。

例如 Nginx、Envoy、云负载均衡等都可能承担这类角色。

“反向”是相对于 forward proxy：forward proxy 代表客户端访问外部。

---

# 17. Load Balancer 是什么

如果有多个后端实例：

```text
API-1
API-2
API-3
```

Load Balancer：

```text
Client
   ↓
  LB
 / | \
1  2  3
```

把流量分配到健康实例。

它解决的是：

- 多实例流量分配；
- 故障实例摘除；
- 可用性/扩缩容入口。

不等于 API Gateway。

---

# 18. API Gateway 是什么

Gateway 通常位于外部客户端和一组内部 API 之间：

```text
Mobile / Web
      ↓
API Gateway
  ├─ Ticket Service
  ├─ User Service
  └─ Agent Service
```

常见横切能力：

- authentication；
- rate limit；
- routing；
- protocol adaptation；
- observability；
- 有限聚合。

危险：

```text
Gateway 逐渐复制每个业务服务的业务规则
```

然后它变成“超级业务服务”。

---

# 19. BFF 是什么

BFF = Backend For Frontend。

为特定客户端形态提供后端入口：

```text
Web BFF
Mobile BFF
```

它可能聚合多个下游，使前端少发请求或得到适合自己的 DTO。

但 BFF 不应该因为方便就：

```text
绕过 owner service 直接改所有业务数据库
```

BFF 主要适配客户端，而不是拥有所有业务事实。

---

# 20. Gateway 与 Reverse Proxy / LB 为什么会重叠

真实产品经常一个组件承担多种角色。

例如某云 Gateway 可能同时：

- reverse proxy；
- load balance；
- auth；
- routing；
- rate limit。

所以不要死背产品分类。

讨论架构时更准确问：

> 这个组件在这套系统里具体负责哪些职责？

---

# 21. 身份在服务之间怎么传播

边缘 Gateway 验证用户 Token：

```text
External Token
↓
Gateway Authentication
↓
Principal(user, tenant, scopes)
```

下游需要知道身份。

危险：

```text
公网用户自己发 X-User-ID: admin
下游直接相信
```

如果通过内部 header/metadata 传播，必须确保：

- Gateway 删除客户端伪造的同名 header；
- 下游只接受可信调用来源；
- service-to-service 也有认证；
- 最终授权仍在拥有资源的服务执行。

Gateway 验过登录，不代表 Ticket Service 可以跳过 owner/tenant 检查。

---

# 22. Service-to-Service Authentication

服务之间也需要回答：

```text
这个请求真的是 Gateway 发的吗？
```

可能使用：

- mTLS；
- workload identity；
- signed service token；
- 云 IAM。

不要把：

```text
来自内网 IP
```

自动等同可信身份。

内网也可能被攻破或错误路由。

---

# 23. Deadline 必须跨服务传播

用户请求总预算：

```text
2 秒
```

Gateway 已经花：

```text
500ms
```

下游不应该重新获得全新的：

```text
2 秒
```

否则链路总时间不断膨胀。

更合理：

```text
剩余 1.5 秒
```

继续向下游传播。

这在 Go `context.Context`、gRPC deadline 中非常常见。

---

# 24. Retry 应该在哪一层

如果每一跳都 retry：

```text
Client x3
Gateway x3
Service A x3
SDK x3
```

会造成 retry amplification。

要明确：

- 哪一层最了解操作是否幂等；
- 哪一层最了解错误是不是暂时性；
- 总 deadline；
- 是否已经有上游 retry。

网络层抽象不能替业务决定重试语义。

---

# 25. Circuit Breaker 是什么问题下才出现

如果一个下游已经持续失败：

```text
每个请求仍然等待 2 秒 timeout
```

会持续浪费资源。

Circuit Breaker 的思想：

```text
失败达到条件
↓
暂时快速拒绝/降级
↓
过一段时间允许少量 probe
↓
恢复后关闭 breaker
```

但它会引入状态和调参。

基础系统先做好：

```text
timeout + bounded concurrency + error handling
```

再根据真实故障考虑 breaker。

---

# 26. Service Discovery 是什么

如果服务实例动态变化：

```text
Service A 到底应该连接哪个 Service B IP？
```

需要稳定名字映射到当前实例。

Kubernetes Service/DNS 就承担一种 service discovery。

不要把 IP 写死在业务代码里。

---

# 27. 分布式事务为什么难

单个 PostgreSQL transaction：

```text
BEGIN / COMMIT
```

可以保护一个数据库事务边界。

如果业务跨：

```text
Order Service DB
Payment Service DB
Inventory Service DB
```

普通本地 transaction 不能一次 rollback 三个独立系统。

这时可能需要：

- workflow/state machine；
- saga/compensation；
- outbox/event；
- idempotency。

所以拆微服务也会让原本简单的 transaction 变成 distributed workflow。

---

# 28. Saga 不要先背模式图

先理解问题：

```text
Step 1 reserve inventory ✅
Step 2 charge payment ✅
Step 3 create shipment ❌
```

不能用一个数据库 transaction 全部 rollback。

所以可能需要补偿：

```text
refund payment
release inventory
```

这类长流程才引出 Saga 类思想。

不要因为“微服务必学 Saga”就一开始做复杂 orchestrator。

---

# 29. Eventual Consistency 是什么

拆成异步事件后：

```text
Ticket 已关闭
Search Index 还没更新
```

短时间内两个系统看到不同状态。

之后消费者处理完成：

```text
Search catches up
```

这叫最终一致的一类场景。

关键是明确：

- 谁是事实源；
- 最长延迟容忍多少；
- 用户会看到什么；
- 消费失败如何修复。

不要用“最终一致”当作所有错误的借口。

---

# 30. 什么时候该保持单体

如果系统：

- 一个小团队；
- 业务边界仍在快速变化；
- 流量不高；
- 发布可以一起；
- 数据 transaction 很多；

模块化单体通常更简单。

你仍然可以练：

- interface boundary；
- domain owner；
- event；
- transaction；
- tests。

等边界成熟再拆，成本更低。

---

# 31. 本仓库综合项目应该怎么演进

旧思路一开始就：

```text
Go Gateway
→ Python Service
→ PostgreSQL
→ Redis
→ Agent
```

会让初学阶段同时处理太多网络边界。

新的合理顺序：

```text
P0: 单个服务 + memory
↓
P1: 单服务 + PostgreSQL
↓
P2: transaction/auth/idempotency
↓
P3: Redis/concurrency（有明确问题才加）
↓
P4: async Worker/Outbox
↓
P5: Agent/RAG
↓
P6: 如果已经能解释边界，再拆 Gateway / 服务
```

拆服务应该成为最后一个实验：

> “我已经知道这个边界为什么值得变成网络边界。”

---

# 32. 如何选择 REST / gRPC / Event

先问语义：

| 问题 | 倾向 |
| --- | --- |
| 外部公开 API，需要 curl/browser 友好 | HTTP/REST |
| 内部强类型 RPC、大量 protobuf 生态 | gRPC 可考虑 |
| 请求必须马上得到结果 | 同步 HTTP/gRPC |
| 事实发生后多个消费者独立处理 | Event |
| 长任务创建后查询状态 | HTTP create/query + async worker |
| 实时单向进度更新 | SSE 可考虑 |
| 全双工实时交互 | WebSocket/gRPC stream 等按场景 |

这不是绝对规则，是决策起点。

---

# 33. 常见误区

## 微服务 = 大型后端必经之路

错误。架构要匹配组织和系统约束。

## 单体 = 没有架构

错误。模块化单体可以有非常清晰的边界。

## gRPC = 比 REST 快所以应该内部全用

过度简化。协议选择还要看调试、兼容、生态和团队能力。

## Event 比同步 API 更解耦，所以都用 Event

错误。很多查询和立即决策更适合同步。

## Gateway 验了 JWT，下游不用鉴权

错误。下游仍需验证可信调用来源和资源授权。

## 共享一个 DB 就不是微服务

不一定；但跨 owner 任意写表会产生强耦合。

## Reverse Proxy / LB / Gateway 是三个永不重叠的产品

错误。真实组件职责会重叠，应描述功能而不是只看产品标签。

---

# 34. 关闭文档复述

1. 单体和“所有代码写一起”为什么不是同一个概念？
2. Modular Monolith 为什么是很好的服务边界训练？
3. 把函数调用变成网络调用后新增哪些失败？
4. 哪些真实原因可能值得拆微服务？
5. Fact Owner / Owner Service 解决什么问题？
6. 为什么共用一个 PostgreSQL 不代表可以互相随便 UPDATE 表？
7. REST 和 gRPC 的主要工程取舍有哪些？
8. 为什么 gRPC 看起来像函数调用却仍必须有 timeout？
9. Event 和 Command 的语义区别是什么？
10. 什么业务更适合同步，什么更适合异步？
11. Reverse Proxy、Load Balancer、API Gateway、BFF 分别强调什么？
12. 为什么公网可伪造的 `X-User-ID` 不能作为下游可信身份？
13. Deadline 为什么需要跨服务传播？
14. 多层 retry 为什么危险？
15. 为什么拆微服务会让本地 transaction 问题升级成 distributed workflow？
16. Eventual Consistency 必须明确哪几个边界？
17. 综合项目为什么应该最后才尝试 Gateway/服务拆分？

如果你面对“要不要拆微服务”的问题，第一反应开始变成“现在具体哪里需要独立边界？”而不是“用不用 gRPC/K8s？”，这节课就达到了目的。
