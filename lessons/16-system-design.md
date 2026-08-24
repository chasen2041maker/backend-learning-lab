# 第 16 课：系统设计——不要从 Redis、Kafka、K8s 开始画架构图

系统设计最常见的错误答案：

```text
用户很多
↓
加 Load Balancer
↓
微服务
↓
Redis
↓
Kafka
↓
Kubernetes
```

看起来“组件很全”，但你不知道：

- 为什么需要这些组件；
- 数据真相在哪里；
- 哪个操作需要事务；
- 重复请求怎么办；
- 某个依赖挂掉会怎样；
- 实际流量是不是根本用不上。

真正的系统设计不是背架构图，而是：

> **从需求和约束，一步一步推导出最小能够满足目标的系统，再针对真实瓶颈增加复杂度。**

---

# 1. 系统设计首先是“定义问题”

用户说：

> 做一个客服工单系统。

这远远不够。

先问：

```text
谁使用？
核心动作是什么？
哪些必须实时？
哪些允许异步？
数据量？
并发？
可用性？
一致性？
安全边界？
明确不做什么？
```

例如第一版：

```text
用户创建工单
查看自己的工单
关闭工单
客服系统 webhook 更新状态
Agent 提供辅助分析
```

明确不做：

```text
支付
复杂实时聊天
全球多区域
千万 QPS
```

“非目标”可以防止方案无限膨胀。

---

# 2. 功能需求和非功能需求分开

## Functional Requirements

系统要做什么：

```text
create ticket
list ticket
close ticket
start agent task
```

## Non-functional Requirements

系统应该具有什么质量：

```text
P95 latency
availability
consistency
security
durability
cost
recovery time
```

例如：

```text
工单创建必须持久，不允许超时重试产生重复
Agent 分析可以慢 30 秒，但任务不能静默丢失
```

这两句就会推导出完全不同的技术边界。

---

# 3. 先估算数量级，不需要装精确

例如：

```text
100,000 tickets/day
```

平均：

```text
100000 / 86400 ≈ 1.16 creates/s
```

即使峰值 100 倍：

```text
≈ 116 creates/s
```

这离“必须 Kafka + 100 个微服务”的结论还很远。

容量估算的目的不是预测到小数点，而是阻止明显过度设计。

---

# 4. 常见要估算什么

## Traffic

```text
requests/day
average QPS
peak QPS
read/write ratio
```

## Data

```text
rows/day
average row size
retention
index size
attachments
```

## External Dependencies

```text
model QPS
provider rate limit
DB connections
Redis capacity
```

## Latency

```text
API target
DB query
model inference
network hops
```

不用一开始非常准，但必须有数量级。

---

# 5. 先画最小正常数据流

不要先画组件大全。

例如创建工单：

```text
Client
  ↓ POST /tickets
API
  ↓ authenticate / validate
Service
  ↓ transaction
PostgreSQL
  ↓ COMMIT
API
  ↓ 201
Client
```

先确保：

```text
这个最基本业务事实如何正确发生
```

然后再添加：

```text
cache
worker
outbox
agent
```

---

# 6. Source of Truth / Owner 必须先定

每类事实问：

```text
谁能最终决定它是什么？
```

例如：

```text
Ticket status -> PostgreSQL / Ticket domain owner
Session -> identity/session system
RAG document -> document owner
Vector index -> derived projection
Cache -> derived state
```

如果多个服务都能随便写同一事实：

```text
状态规则迟早漂移
```

---

# 7. Data Model 是架构的一部分

系统设计不是只画 boxes/arrows。

至少要知道：

```text
tickets
id
tenant_id
status
version
created_at
```

为什么有：

```text
tenant_id
```

因为所有资源需要租户隔离。

为什么有：

```text
version
```

因为并发更新需要冲突检测。

字段和 constraint 本身就是架构决策。

---

# 8. API Contract 先于具体框架

例如：

```http
POST /api/v1/tickets
Idempotency-Key: ...
Authorization: Bearer ...
```

Body：

```json
{
  "title": "无法登录"
}
```

注意没有：

```json
{"tenant_id":"..."}
```

因为 tenant 来自可信 Principal。

这里已经决定：

- identity boundary；
- idempotency boundary；
- public contract。

还没选 Gin/FastAPI。

---

# 9. 失败窗口才是真正区分方案质量的地方

正常流程谁都能画。

需要逐个问：

```text
在这里宕机会怎样？
```

创建请求：

```text
validate
↓
INSERT
↓
COMMIT
↓
write response
```

关键窗口：

```text
COMMIT 后 response 前宕机
```

这会直接推导：

```text
Idempotency
```

所以可靠性组件应该从失败窗口推导，而不是从“最佳实践清单”加入。

---

# 10. Consistency 要具体说“哪两个状态”

不要只说：

```text
我们需要强一致 / 最终一致
```

问：

> 哪两个观察者、哪两份状态、允许多久不同？

例如：

```text
PostgreSQL ticket status
和
Redis cache ticket status
```

允许几十秒 stale？

可能可以。

但：

```text
账户余额
和
扣款判断
```

可能不能接受 stale。

一致性不是全系统一个开关。

---

# 11. Availability 也不是一句“99.99%”

要问：

```text
哪个功能？
什么时间窗口？
失败定义是什么？
依赖怎么算？
```

例如：

```text
工单创建 SLO 99.9%
Agent 辅助分析 99%
```

可能比要求所有功能统一 99.999% 更符合成本。

不同业务能力可以有不同 SLO。

---

# 12. CAP 不要拿来解释所有设计

CAP 讨论的是分布式数据系统在网络分区下：

```text
Consistency
Availability
Partition tolerance
```

它不是：

```text
任何系统只能在一致性/可用性里二选一
```

也不是一个选择数据库的万能口诀。

基础系统设计更应该先具体说明：

- 数据 owner；
- transaction；
- replica lag；
- failure policy；
- stale tolerance。

不要用 CAP 三个字母代替具体分析。

---

# 13. Cache 什么时候才应该加入

起点：

```text
Client -> API -> PostgreSQL
```

先看指标。

如果：

```text
read QPS 高
某个查询成为 DB 瓶颈
数据允许短时间 stale
```

才考虑：

```text
Redis Cache
```

然后必须重新回答：

```text
cache miss 怎么办？
TTL？
更新后怎么失效？
Redis 挂了怎么办？
回源会不会击穿 DB？
```

新增组件永远同时新增失败模式。

---

# 14. Queue / Async 什么时候加入

如果一个操作：

```text
必须在当前 HTTP response 里完成吗？
```

如果不需要，例如：

```text
发通知
生成报告
慢 Agent Task
```

可以异步。

加入 Queue/Worker 后又要处理：

```text
重复
ACK
Pending
backlog
retry
DLQ
```

所以异步不是免费解耦。

---

# 15. Outbox 什么时候加入

当一个数据库 transaction 完成以后必须可靠触发异步事件：

```text
UPDATE ticket
+
publish ticket.closed
```

跨 PostgreSQL 和 Broker 双写不可靠。

这时才有明确问题推导：

```text
Transactional Outbox
```

如果系统没有这种双写需求，不需要为了“架构完整”先加 Outbox。

---

# 16. 微服务什么时候才加入

先问单体哪里不够：

```text
独立部署？
团队 ownership？
独立扩缩？
安全边界？
技术运行环境？
```

如果答案只是：

```text
以后可能大
```

通常不够。

拆服务会新增：

- 网络失败；
- service auth；
- distributed tracing；
- API compatibility；
- distributed workflows。

复杂度必须换来具体收益。

---

# 17. Database Scaling 不要第一反应就是 Sharding

先后顺序通常可以是：

```text
SQL correctness
↓
indexes
↓
query optimization
↓
connection pool
↓
cache where justified
↓
read replica where justified
↓
partitioning
↓
真正达到单节点/单集群边界再讨论 sharding
```

Sharding 会引入：

- shard key；
- rebalancing；
- cross-shard query；
- distributed transaction；
- operational complexity。

不要用规模想象提前购买复杂度。

---

# 18. Read Replica 解决什么

如果：

```text
读远多于写
主库读压力明显
```

可以把一部分读放 replica。

但 replica 通常可能有 lag：

```text
刚写主库
立即读 replica
→ 可能还看不到
```

所以加入 replica 后要定义：

- 哪些读允许 stale；
- read-your-writes 是否需要；
- failover；
- connection routing。

---

# 19. Sharding 的第一问题是 Shard Key

例如：

```text
shard by tenant_id
```

可以让一个 tenant 的数据集中在某 shard。

但如果一个超级 tenant 占 50% 流量：

```text
hot shard
```

所以 shard key 要结合：

- 数据分布；
- 访问模式；
- cross-tenant query；
- growth。

Sharding 不是“数据太多就 id % 10”。

---

# 20. Load Balancer 的容量不是系统容量

API 可以水平扩：

```text
3 -> 30 instances
```

但 PostgreSQL：

```text
connection limit
CPU
IO
```

没变。

甚至：

```text
30 instances × 50 DB connections
= 1500 connections
```

扩 API 可能把 DB 压垮。

系统容量由最紧的瓶颈决定。

---

# 21. Little's Law 给后端一个很有用的直觉

在稳定系统里可用近似关系：

```text
L = λW
```

其中：

```text
L = 系统中平均并发中的工作量
λ = 到达速率
W = 平均停留时间
```

例如：

```text
100 requests/s
平均请求 0.5s
```

大约有：

```text
50 concurrent requests
```

如果 latency 变成 5s：

```text
约 500 concurrent requests
```

即使 QPS 没变，慢依赖也会让同时占用资源的请求暴增。

这解释了为什么 timeout、连接池和背压如此重要。

---

# 22. Queue 同样需要容量估算

Producer：

```text
1000 jobs/s
```

Consumer：

```text
800 jobs/s
```

每秒积压：

```text
200
```

一小时：

```text
720,000 jobs
```

这不是“以后慢慢处理”。

系统会无限落后。

必须：

- 提升消费；
- 限制生产；
- 降级；
- 扩容；
- 改处理成本。

---

# 23. Back-of-the-envelope Storage 估算

假设：

```text
1,000,000 tickets/year
平均每行及索引/元数据粗略 2 KB
```

约：

```text
2 GB/year（这里只是数量级示意）
```

即使再放大几倍，仍可能轻松由 PostgreSQL 管理。

如果附件平均 10 MB：

```text
1,000,000 × 10 MB
≈ 10 TB
```

这时附件就不应该直接当普通表字段处理，Object Storage 变得合理。

系统设计就是通过数量级让组件选择有依据。

---

# 24. Object Storage 为什么用于大文件

文件：

```text
图片
PDF
视频
模型产物
```

通常更适合：

```text
S3-style object storage
```

数据库保存：

```text
object key
metadata
owner
status
```

而不是每次都把巨大二进制塞在核心事务表里。

但文件上传还会新增：

- size limit；
- MIME validation；
- malware scan；
- presigned URL；
- orphan cleanup；
- permission。

---

# 25. Search Engine 什么时候才需要

PostgreSQL 已经支持很多搜索能力。

如果需求只是：

```text
按 ID/状态/时间过滤
```

没必要先上 Elasticsearch/OpenSearch。

真正出现：

- 大规模全文检索；
- relevance ranking；
-复杂聚合；
- 独立搜索扩缩；

才考虑专门搜索引擎。

然后搜索 index 成为派生投影，需要：

```text
同步
重建
删除
权限
```

---

# 26. Multi-region 为什么非常晚才学

多区域会涉及：

- latency；
- data replication；
- conflict；
- failover；
- consistency；
- DNS/routing；
- cost；
- compliance。

如果业务没有跨洲低延迟或区域级灾备要求，不应该先设计全球 active-active。

先把单区域恢复、备份和 SLO 做明白。

---

# 27. RPO / RTO 是恢复设计的两个核心词

## RPO

Recovery Point Objective：

> 最多可以丢多长时间的数据？

例如：

```text
RPO = 5 min
```

意味着灾难时允许最多约 5 分钟的数据窗口损失。

## RTO

Recovery Time Objective：

> 故障以后多快要恢复服务？

例如：

```text
RTO = 30 min
```

备份策略要从 RPO/RTO 反推，而不是：

```text
我们每天 backup 一次，应该够吧
```

---

# 28. Security 要从架构一开始进入

不要最后加一张：

```text
Security
```

设计每条数据流都问：

```text
谁调用？
身份从哪来？
能访问哪个 tenant？
Secret 放哪？
哪些数据敏感？
日志会不会泄露？
是否有 SSRF/注入？
副作用能否重放？
```

安全是系统约束，不是外部插件。

---

# 29. Observability 也应该在设计阶段出现

每个关键组件问：

```text
如果它变慢，我怎么知道？
如果 backlog 堆积，我看什么？
如果一条请求跨服务失败，我怎样关联？
```

例如：

```text
HTTP RED
DB pool wait
Outbox oldest age
Agent provider latency/cost
```

没有观测的架构，故障后只能猜。

---

# 30. Failure Mode Table 很实用

设计一个组件时可以写：

| 组件/步骤 | 失败 | 用户看到 | 系统恢复 |
| --- | --- | --- | --- |
| PostgreSQL | timeout | 503 | 不盲目重试非幂等操作 |
| Redis cache | unavailable | 可能变慢 | 有界回源 DB |
| Model | timeout | task failed/partial | 按 policy retry/fallback |
| Outbox publisher | crash | event 延迟 | 从 DB pending 恢复 |

这种表比“高可用设计”四个字具体得多。

---

# 31. Trade-off 才是系统设计核心

任何方案都有成本。

例如 Cache：

```text
+ 降低 DB read latency/load
- stale data
- invalidation complexity
- Redis dependency
```

Microservice：

```text
+ independent deploy/scale
- network/ops/distributed consistency
```

Async：

```text
+ decouple latency / absorb burst
- duplicate/order/backlog/eventual consistency
```

好的设计不是“没有缺点”，而是：

> 缺点在当前需求下可接受，并且你知道它是什么。

---

# 32. 一个简化系统设计流程

以后面试/评审都可以使用：

```text
1. 用户和核心用例
2. 非目标
3. 流量 / 数据 / SLO 数量级
4. API / Event contract
5. 数据模型 / source of truth / owner
6. 正常数据流
7. transaction / idempotency / concurrency
8. failure windows / recovery
9. security boundaries
10. observability / tests
11. 找当前瓶颈
12. 只为瓶颈引入新组件
13. 记录 trade-off 和未解决风险
```

顺序可以调整，但不要一上来直接说组件名。

---

# 33. 系统设计面试里怎么讲“为什么不用 X”

这其实很加分。

例如：

> 当前峰值约 100 writes/s，PostgreSQL 有明确索引和事务需求。我先用单主数据库。当前没有证据需要 sharding；引入 sharding 会增加跨 shard transaction 和运维复杂度。如果后续写入、存储或单租户热点达到瓶颈，再基于监控数据评估 partition/sharding。

这比：

```text
我们用 MongoDB 因为 scalable
```

具体得多。

---

# 34. 一个工单系统怎样逐步长出来

## Version 0

```text
Go API
+ memory repo
```

学 HTTP/分层。

## Version 1

```text
Go/Python API
+ PostgreSQL
```

学事实、SQL、约束。

## Version 2

```text
+ auth
+ transaction
+ optimistic lock
+ idempotency
```

学正确性。

## Version 3

如果读热点真实出现：

```text
+ Redis cache
```

## Version 4

如果后续通知/任务不应阻塞请求：

```text
+ Outbox
+ Worker
```

## Version 5

如果有 Agent 分析：

```text
+ Agent Task
+ RAG
+ model/tool budgets
```

## Version 6

如果模块真的需要独立运行：

```text
+ Gateway / service split
```

这就是“从问题推导复杂度”。

---

# 35. 本仓库最终综合项目怎么用

查看：

```text
projects/reliable-support-agent/
```

它现在应该是一个演进实验，不是一张必须一次实现的架构图。

每阶段都要回答：

```text
上一阶段存在什么真实限制？
这一阶段新增什么能力？
新增组件又引入什么失败？
如何验证？
```

如果不能解释一个组件为什么存在，就先不加。

---

# 36. 常见系统设计误区

## 高并发 = Redis + Kafka

错误。先算数量级和瓶颈。

## 大数据 = MongoDB/分库分表

错误。先看访问模式和 PostgreSQL 边界。

## 高可用 = 多副本

不够。数据故障、依赖故障、部署错误、区域故障还需要具体恢复设计。

## 微服务 = 可扩展

过度简化。微服务主要改变服务/组织边界，也增加运行时复杂度。

## Cache = 性能提升，不影响正确性

错误。多一份状态就多一致性问题。

## Queue = 解耦，所以一定更可靠

错误。它引入 duplicate/order/backlog/recovery 问题。

## K8s = 系统架构

错误。K8s 是运行/编排层，不替你设计业务和数据一致性。

## “支持千万 QPS”越大越好

错误。没有需求依据的数量只是过度设计。

---

# 37. 关闭文档复述

1. 为什么系统设计第一步不是选数据库？
2. Functional 和 Non-functional requirements 有什么区别？
3. 容量估算为什么只要数量级也很有价值？
4. Source of Truth / Owner 为什么必须先明确？
5. 为什么 Data Model 也是架构？
6. “强一致”为什么必须说清是哪两份状态之间？
7. 为什么 Cache 应该从真实读瓶颈推导？
8. 为什么 Queue/Async 会增加新的可靠性问题？
9. 为什么 Outbox 只有出现 DB + Broker 双写问题时才有价值？
10. 微服务应该由哪些真实需求驱动？
11. 为什么数据库优化通常不应该直接跳到 Sharding？
12. Read Replica 会引入什么读一致性问题？
13. Little's Law 如何解释慢请求导致并发资源暴涨？
14. 为什么 API 横向扩容可能压垮数据库？
15. RPO 和 RTO 分别回答什么？
16. Failure Mode Table 为什么比“高可用”更具体？
17. Trade-off 为什么是系统设计核心？
18. 一个组件“暂时不用”的理由为什么也是设计能力？

最终你应该能够面对一张架构图，逐个指着组件回答：

> **它解决了前一版的哪个具体问题；如果删除它会发生什么；它自己又引入了什么失败和成本。**

做到这一点，系统设计才不再是背答案。
