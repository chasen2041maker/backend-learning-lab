# 第 9 课：异步任务、消息、Outbox、Redis Streams 和“至少一次”

同步 HTTP 很容易理解：

```text
Client 发请求
Server 做完
Server 返回
```

但很多工作不适合让客户端一直等：

- 发邮件；
- 生成报告；
- 调用慢模型；
- 批处理；
- 通知多个下游；
- 对外部事件做后续处理。

于是出现异步任务和消息。

真正难的不是“把消息发进队列”，而是：

> **消息可能重复、延迟、乱序，Worker 可能在任何一步崩溃。业务怎么仍然正确？**

---

# 1. 为什么需要异步

同步链路：

```text
Client
  ↓
API
  ↓
Database
  ↓
Email Provider
  ↓
Analytics
  ↓
Model
  ↓
Response
```

问题：

```text
任意一个下游慢
→ Client 全部跟着等
```

而且同步链越长：

```text
整体失败概率越高
```

有些操作可以改成：

```text
Client
  ↓
API
  ↓
保存任务 / 业务事实
  ↓
202 Accepted / 201

后台 Worker
  ↓
慢操作
```

这叫把工作解耦到异步路径。

---

# 2. Queue / Stream / Job 先分语义

## Job

通常表示：

> 有一项工作等待某个 Worker 执行。

例如：

```text
generate-report job
```

## Message / Event

通常表示：

```text
发生了一个事实
```

例如：

```text
ticket.closed
```

多个消费者可能都感兴趣。

## Queue

强调：

```text
待处理工作
```

通常一项工作由某个消费者处理。

## Stream / Log

强调按顺序追加的消息记录，可以有：

- consumer groups；
- replay；
- position / ID。

实际产品的语义会不同，不要只按名字判断。

---

# 3. 为什么“消息发成功”也不等于业务完成

流程：

```text
Producer
→ Message System
→ Consumer
→ Database
```

可能在任何位置失败。

例如：

```text
Consumer 收到消息
↓
UPDATE Database ✅
↓
准备 ACK
↓
💥 Consumer 崩溃
```

消息系统不知道数据库已经更新。

于是消息以后可能再次投递。

如果第二次处理会再次扣款/发货：

```text
业务重复
```

所以异步系统必须默认考虑：

> **重复投递。**

---

# 4. At-most-once / At-least-once

## At-most-once

最多处理一次。

可能：

```text
消息丢了就丢了
```

适合某些低价值 telemetry，但核心业务通常很难接受。

## At-least-once

至少投递一次。

优点：

```text
不容易静默丢工作
```

代价：

```text
可能重复
```

所以 Consumer 必须幂等。

大多数可靠业务消息系统更常见的是：

```text
at-least-once + idempotent consumer
```

---

# 5. Exactly-once 为什么要非常谨慎

很多系统宣传“exactly once”，但要问清楚范围。

可能只是：

```text
消息系统内部某段 pipeline
```

而你的业务最终还有：

```text
数据库
邮件
支付
第三方 API
```

只要跨多个系统，就必须重新分析失败窗口。

工程上更安全的默认心智模型：

> 消息可能重复；业务副作用必须有自己的幂等边界。

---

# 6. ACK 是什么

ACK = acknowledgement。

Consumer 告诉消息系统：

```text
这条消息我已经成功完成处理
```

最重要的问题：

> **什么时候 ACK？**

---

# 7. 太早 ACK 会怎样

```text
收到消息
↓
立即 ACK ✅
↓
开始更新 DB
↓
💥 崩溃
```

消息系统认为：

```text
已经完成
```

但数据库：

```text
没有完成
```

消息可能永远不再投递。

所以核心业务一般不能在副作用完成前随便 ACK。

---

# 8. 业务提交后再 ACK 会怎样

```text
收到消息
↓
BEGIN
UPDATE DB
COMMIT ✅
↓
ACK
```

如果：

```text
COMMIT 后
ACK 前
崩溃
```

消息以后会重投。

这没有办法仅靠调整 ACK 时机彻底避免。

因此：

```text
Consumer 必须识别重复
```

---

# 9. Consumer Idempotency

每个 event 有唯一：

```text
event_id
```

Consumer transaction：

```text
BEGIN

INSERT processed_events(event_id)
-- UNIQUE

应用业务变化

COMMIT
```

重复消息：

```text
processed_events 已存在
→ 不再次应用副作用
```

关键：

> “记录已处理”和“业务变化”最好在同一个事实事务里完成。

否则仍可能有窗口。

---

# 10. Producer 端也有一个经典双写问题

业务：关闭工单，并发布：

```text
ticket.closed
```

错误顺序 A：

```text
UPDATE PostgreSQL ✅
PUBLISH Redis ❌
```

结果：

```text
事实已变
事件丢失
```

错误顺序 B：

```text
PUBLISH Redis ✅
UPDATE PostgreSQL ❌
```

结果：

```text
消费者看到一个实际上没有提交的事实
```

这就是 Dual Write Problem。

---

# 11. Transactional Outbox 是什么

不直接尝试把 PostgreSQL 和 Redis “一起 transaction”。

而是先只让 PostgreSQL transaction 负责它能原子保护的事实：

```text
BEGIN

UPDATE tickets

INSERT outbox_events(
  event_id,
  event_type,
  payload,
  created_at
)

COMMIT
```

这样：

```text
工单更新存在
↔
outbox event 一定也存在
```

或者两者一起不存在。

---

# 12. Publisher 再负责把 Outbox 发出去

```text
PostgreSQL outbox
      ↓
Publisher
      ↓
Redis Streams / Kafka / other broker
```

如果 Redis 挂了：

```text
outbox row 还在 DB
```

等 Redis 恢复再继续。

这比：

```text
业务 transaction 里直接调用 Redis
```

更容易恢复。

---

# 13. Publisher 自己也会重复发布

失败窗口：

```text
Publisher 读取 outbox event
↓
XADD Redis ✅
↓
准备标记 PostgreSQL published
↓
💥 崩溃
```

重启后：

```text
数据库仍认为未发布
→ 再次 XADD
```

于是消息重复。

所以 Outbox **没有消灭重复**。

它解决的是：

> 数据库事实提交后，待发布事件不会因为跨系统双写窗口彻底消失。

Consumer 仍然要幂等。

---

# 14. Outbox 状态大概是什么样

```text
pending
↓
publishing / claimed
↓
published
```

真实实现可能有：

```text
attempt_count
next_attempt_at
lease_until
claimed_by
last_error
published_at
```

不要一开始就把所有字段都加满。

先从：

```text
能恢复重复 publish
```

开始，再根据并发 Publisher 需求引入 claim/lease。

---

# 15. 多个 Publisher 怎么避免同时处理同一行

假设两个 publisher：

```text
P1
P2
```

同时看到同一 pending row。

可能需要：

- `FOR UPDATE SKIP LOCKED`；
- claim column；
- lease；
- conditional update。

具体方案取决于数据库和吞吐。

重要的是：

> ownership 必须由一个原子操作建立，而不是两个 Worker 先 SELECT 后都“觉得自己拥有”。

---

# 16. Lease 是什么

长期任务不能永久属于一个 Worker。

否则 Worker 崩溃：

```text
任务永远卡住
```

Lease：

```text
Worker A 拥有任务
直到 12:00:10
```

如果 A 没完成：

```text
12:00:10 后
Worker B 可以接管
```

这让故障恢复成为可能。

---

# 17. Lease 又会引入 stale worker

场景：

```text
A 拿 lease
A 卡住
lease 过期
B 接管
A 又恢复
```

现在 A、B 都可能继续执行。

这叫 stale worker 问题。

不能只靠：

```text
“理论上 A 超时后应该停止”
```

因为进程可能暂停、网络分区、GC、系统卡顿。

---

# 18. Fencing Token

每次新的 lease 获得一个更大的 token：

```text
A -> token 41
B -> token 42
```

下游写入必须带 token。

事实库记住最新 token：

```text
42
```

A 恢复后用 41 写：

```text
拒绝
```

这叫 fencing。

它不是 Redis 特有概念，而是“旧 owner 不应该覆盖新 owner”这种通用并发保护。

---

# 19. Redis Streams 是什么

Stream 可以先理解为：

```text
按 ID 追加的消息日志
```

Producer：

```text
XADD stream ...
```

Consumer Group：

```text
多个 consumer
协作处理一条 stream
```

简化：

```text
Stream
  |
  +-> Group: workers
        |
        +-> Consumer A
        +-> Consumer B
```

---

# 20. Consumer Group 不是广播给每个人

同一 group 内：

```text
消息通常分配给组内某个 consumer 处理
```

如果两个不同业务都需要各自看到所有消息：

```text
notification group
analytics group
```

可以使用不同 group。

所以：

```text
consumer
和
consumer group
```

要分清。

---

# 21. Pending 是什么

Consumer Group 把一条消息交给 Consumer A：

```text
已投递
但还没 ACK
```

这条消息处于 Pending。

Redis 会记录：

```text
谁拿了
多久没 ACK
投递次数等
```

如果 A 崩了：

```text
Pending 不应该永远卡死
```

其他 consumer 可以 reclaim/claim。

---

# 22. `XAUTOCLAIM` 解决什么

它可以帮助接管：

```text
空闲时间已经超过阈值的 Pending message
```

概念：

```text
A 拿到消息
↓
A 崩了
↓
消息 idle 60s
↓
B reclaim
```

但 reclaim 后消息又执行一次，所以 Consumer Idempotency 仍然必要。

---

# 23. Message Ordering 不要想当然

你可能发：

```text
ticket.created
 ticket.closed
```

但不同 partition / consumer / retry 场景下，消费者看到的顺序未必永远符合你的业务期待。

如果顺序重要，需要设计：

- per-entity sequence；
- version；
- partition key；
- stale event rejection。

例如：

```text
current version=5
收到 event version=4
→ stale
→ 不应该把状态回滚
```

---

# 24. DLQ 是什么

某条消息一直失败：

```text
attempt 1
attempt 2
attempt 3
...
```

无限 retry 会：

- 消耗资源；
- 阻塞正常任务；
- 制造日志噪声。

所以达到策略上限后，可以进入 DLQ：

```text
Dead Letter Queue
```

但 DLQ 不是“垃圾桶”。

必须有：

```text
告警
诊断
修复数据/代码
安全重放
审计
```

否则只是把失败藏起来。

---

# 25. Retry Policy 要有预算

异步任务重试：

```text
attempt 1
↓
backoff
↓
attempt 2
```

需要：

- 哪些错误可重试；
- max attempts；
- total age / deadline；
- backoff；
- jitter；
- DLQ threshold。

不能：

```text
while true:
    try again
```

---

# 26. Queue Backlog 是系统健康信号

如果生产速度：

```text
1000 msg/s
```

消费：

```text
100 msg/s
```

即使所有 consumer 都没有报错：

```text
系统仍然在失败
```

因为 backlog 越来越大。

所以要看：

- backlog count；
- oldest message age；
- Pending count；
- Pending oldest age；
- retry rate；
- DLQ rate。

这就是异步系统的 observability。

---

# 27. SSE 和异步任务是什么关系

Agent Task 可能：

```text
POST /tasks
→ 202 + task_id
```

后台执行。

前端想看进度：

```text
SSE
```

可以流式接收进度。

但 SSE 连接断开不应该让业务任务“事实消失”。

正确边界：

```text
任务状态持久化
SSE 只是实时观察通道
```

断线后仍可：

```text
GET /tasks/{id}
```

恢复终态。

---

# 28. Async 不等于一定用消息队列

一个简单系统可能：

```text
PostgreSQL jobs table
+ Worker polling
```

就足够。

不要形成：

```text
异步任务 = Kafka
```

或：

```text
消息 = Redis Streams
```

组件选择要由：

- 吞吐；
- 保留时间；
- replay；
- 多消费者；
- 运维能力；
- 现有基础设施。

决定。

---

# 29. 本仓库实验顺序

建议按照问题逐步跑，而不是一次理解所有命令。

## 实验 1：单 Consumer

写入一条 Stream 消息，读取并 ACK。

先确认：

```text
消息的生命周期
```

## 实验 2：ACK 前崩溃

```text
收到 message
业务成功
进程在 ACK 前退出
```

重启后观察 Pending/reclaim。

## 实验 3：重复处理

让同一 `event_id` 到达两次，证明业务结果只产生一次。

## 实验 4：Outbox Publisher

模拟：

```text
publish 成功
但 published_at 没写成功
```

再次运行 Publisher，观察重复 publish，并由 Consumer 幂等兜底。

## 实验 5：Lease/Fencing

使用：

```text
exercises/reliability-labs/outbox_worker.py
```

证明旧 worker 在新 owner 接管后不能写旧结果。

---

# 30. 常见误区

## 上了 Queue 就不会丢任务

错误。

要分析 Producer、Broker、Consumer 和业务 DB 每个失败窗口。

## ACK 越早越高性能，所以越好

错误。

ACK 时机是正确性语义。

## Outbox = exactly once

错误。

Outbox 主要解决数据库事实和“待发布意图”的原子持久化；publish/consume 仍可能重复。

## Consumer Group = 所有 Consumer 都收到一份

错误。

同一 group 内通常协作分担消息。

## Pending 表示失败

不一定。

它表示已投递尚未 ACK，可能正在正常处理，也可能 consumer 已崩。

## DLQ 就算处理完失败

错误。

DLQ 是隔离和人工/自动恢复流程的入口。

## 有 Redis Streams 就应该把业务状态也放 Redis

错误。

消息传输角色和事实存储角色必须分开。

---

# 31. 关闭文档复述

1. 为什么有些工作适合从 HTTP 同步链路移到异步？
2. Job、event、queue、stream 分别强调什么语义？
3. At-least-once 的代价是什么？
4. 为什么“exactly once”不能只看 Broker 宣传？
5. ACK 太早会怎样？
6. 为什么 COMMIT 后 ACK 前崩溃会导致消息重投？
7. Consumer Idempotency 应该保护什么？
8. Dual Write Problem 是哪两个系统之间的不一致？
9. Transactional Outbox 真正保证了什么，又没有保证什么？
10. Publisher 为什么仍可能重复发布？
11. Lease 为什么需要 expiry？
12. Fencing Token 为什么能阻止 stale worker？
13. Redis Streams Consumer Group 和 Consumer 的关系是什么？
14. Pending / reclaim 的意义是什么？
15. 为什么乱序事件需要 entity version/sequence？
16. DLQ 为什么不是垃圾桶？
17. 为什么 backlog age 比单纯“Worker 没报错”更能说明系统是否跟得上？
18. 为什么 SSE 断开不应该影响任务真实状态？

如果能画出“数据库事务 → Outbox → Publisher → Stream → Consumer → DB → ACK”的完整失败链路，你已经真正进入可靠异步后端的核心了。
