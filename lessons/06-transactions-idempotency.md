# 第 6 课：事务、并发更新与幂等——数据库已经提交，但客户端不知道怎么办

如果第 5 课解决的是“事实放哪里”，本课解决的是：

> **多个事实一起变化、多个请求同时变化、请求重复到达时，怎样避免业务状态变乱？**

这是后端最重要的一组基础能力之一。

---

# 1. Transaction 为什么存在

假设“关闭工单”需要做三件事：

```text
1. tickets.status = closed
2. 写 audit_log
3. 写 outbox_event
```

如果逐条独立执行：

```text
UPDATE ticket       ✅
INSERT audit        ✅
INSERT outbox       ❌
```

结果：

```text
工单已经关闭
但系统永远没有生成后续事件
```

业务进入“半完成状态”。

Transaction 的目标就是让一组数据库操作形成一个提交边界：

```text
BEGIN
  UPDATE ticket
  INSERT audit
  INSERT outbox
COMMIT
```

要么一起提交，要么失败时回滚。

---

# 2. ACID 不要只背四个单词

## Atomicity：原子性

一组事务内的数据库变化：

```text
全部提交
或者
全部不提交
```

不是说 CPU 指令原子，也不是说外部 HTTP 请求能自动回滚。

## Consistency：一致性

事务执行前后，数据库应该继续满足定义好的不变量：

```text
constraint
foreign key
业务状态规则
```

数据库本身只能保护它知道的规则；业务规则仍要由 Service/transaction code 正确实现。

## Isolation：隔离性

多个事务同时执行时，不能简单把它们想成完全互不影响。

数据库提供不同隔离级别，让你在：

```text
并发性能
vs
看到多少并发中间状态
```

之间做权衡。

## Durability：持久性

事务确认提交后，数据库应该把它作为已提交事实可靠保存，即使之后进程崩溃。

这不等于：

```text
跨机房永不丢数据
```

备份、复制、磁盘故障、灾备仍然是另外的问题。

---

# 3. Transaction 只能保护数据库里的东西

非常重要。

错误想象：

```text
BEGIN
UPDATE database
send email
call payment API
COMMIT
```

如果邮件已经发出去，随后数据库 rollback：

```text
数据库回滚了
邮件不会自动飞回来
```

数据库事务无法自动回滚：

- HTTP 请求；
- 邮件；
- Redis 写入；
- 消息系统发布；
- 大模型调用；
- 第三方支付。

所以不要把长时间外部调用放在持有数据库锁的事务里。

后面 Outbox 就是为了解决“数据库事实 + 外部消息”这类边界。

---

# 4. COMMIT 是一个非常重要的时间点

一次请求可能是：

```text
Client
  |
  | POST /tickets
  v
Server
  |
  | BEGIN
  | INSERT
  | COMMIT
  |
  | write HTTP response
  v
Client
```

注意：

```text
Database COMMIT
```

和：

```text
Client 收到 201
```

不是同一个时刻。

中间存在失败窗口。

---

# 5. 后端经典失败窗口：提交成功，但响应丢了

时间线：

```text
Client -> POST create ticket
Server -> INSERT ticket
Server -> COMMIT ✅
Server -> 准备返回 201
Server -> 💥 宕机
Client -> timeout
```

客户端看到的是：

```text
“请求失败 / 超时”
```

但数据库里：

```text
工单已经创建成功
```

客户端通常会怎么办？

```text
重试
```

如果服务器把第二次当全新请求：

```text
ticket A
 ticket B
```

重复创建。

这就是为什么可靠后端必须理解：

> **客户端看到失败，不代表服务端一定没做。**

---

# 6. Idempotency 是什么

幂等的业务含义：

> 同一个逻辑操作被重复提交，最终外部业务结果仍然只发生一次。

例如：

```text
Idempotency-Key: create-ticket-001
```

第一次：

```text
key 不存在
→ 创建 ticket_123
→ 保存 key -> ticket_123 / response
→ COMMIT
```

第二次相同 key：

```text
发现已经处理
→ 不再创建新 ticket
→ 返回之前结果
```

于是：

```text
客户端重试 5 次
业务仍只有一个 ticket
```

---

# 7. 幂等不是“接口返回一样就行”

真正要保护的是副作用。

比如错误实现：

```text
每次请求都扣款
但最后返回同一个 JSON
```

HTTP 响应看起来一样，但业务已经扣了两次。

所以幂等的观察对象是：

```text
业务事实和副作用
```

而不是单纯 response body。

---

# 8. Idempotency Key 不能只放内存

如果：

```text
process memory:
create-ticket-001 -> ticket_123
```

服务重启：

```text
记录没了
```

客户端重试仍然可能重复创建。

核心业务幂等通常需要持久化：

```text
PostgreSQL unique constraint
```

例如：

```sql
CREATE TABLE idempotency_records (
    tenant_id text NOT NULL,
    key text NOT NULL,
    request_hash text NOT NULL,
    resource_id uuid,
    response_status integer,
    response_body jsonb,
    PRIMARY KEY (tenant_id, key)
);
```

这里 tenant 也进入 key 空间，避免不同租户互相占用同一个客户端 key。

---

# 9. 为什么还需要 request hash

攻击者/客户端可能：

第一次：

```text
Idempotency-Key: abc
Body: {"title":"A"}
```

第二次：

```text
Idempotency-Key: abc
Body: {"title":"完全不同的 B"}
```

如果服务器只看 key，然后直接返回旧结果，客户端很难发现自己错误复用了 key。

一种做法：保存规范化请求的 hash。

重复 key 时：

```text
same key + same request hash
→ replay previous result

same key + different request hash
→ conflict / explicit error
```

---

# 10. 并发请求为什么比顺序请求难

顺序：

```text
Request A 完成
然后 Request B
```

很好推理。

并发：

```text
Request A ---- read ---- write
Request B ------ read ---- write
```

步骤可能交错。

这会产生 race condition。

---

# 11. Lost Update：最经典的数据库并发问题

初始：

```text
version = 1
status = open
```

Request A：

```text
读取 version=1
准备 close
```

Request B：

```text
也读取 version=1
准备 change priority
```

如果两边最后都直接“整行覆盖”：

```text
A write
B write
```

B 可能覆盖 A 的变化。

这叫 lost update。

---

# 12. Optimistic Lock：我先假设冲突不常发生

常见做法：增加：

```text
version
```

更新：

```sql
UPDATE tickets
SET status = $1,
    version = version + 1
WHERE id = $2
  AND tenant_id = $3
  AND version = $4;
```

例如：

```text
我读到 version=5
```

只有数据库仍然是：

```text
version=5
```

更新才成功。

如果别人先改了：

```text
version=6
```

你的 UPDATE：

```text
0 rows affected
```

这不是普通“数据库坏了”，而是：

```text
并发冲突
```

应用需要决定：

- 返回 409；
- 重新读取让用户决定；
- 某些安全场景有限重试。

---

# 13. Pessimistic Lock：先把数据锁住

例如：

```sql
SELECT *
FROM tickets
WHERE id = $1
  AND tenant_id = $2
FOR UPDATE;
```

其他竞争事务可能需要等待。

适合：

- 冲突概率高；
- 必须先读当前状态再决定复杂写入；
- 临界区可以保持很短。

风险：

```text
等待
阻塞
lock timeout
deadlock
吞吐下降
```

所以不是“悲观锁更安全，因此全部用悲观锁”。

---

# 14. Deadlock 是什么

Transaction A：

```text
先锁 row 1
再等 row 2
```

Transaction B：

```text
先锁 row 2
再等 row 1
```

形成：

```text
A 等 B
B 等 A
```

数据库通常会检测到 deadlock，并主动终止其中一个事务。

这意味着应用必须接受一个事实：

> 正确并发系统里，某些 transaction 失败并要求重试可能是正常现象。

降低 deadlock：

- 固定加锁顺序；
- transaction 尽量短；
- 不在 transaction 内做慢外部调用；
- 只对明确可重试数据库错误有限重试。

---

# 15. Isolation Level 是什么

不同事务并发执行时，你允许它看到什么？

PostgreSQL 常见：

```text
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

基础阶段不需要死背所有 anomaly 名称，但要理解：

```text
隔离越强
通常越容易限制并发 / 产生 serialization retry
```

PostgreSQL 默认：

```text
READ COMMITTED
```

每个 statement 会看到开始执行时已经提交的数据快照。

如果业务需要更强的不变量，不要仅靠“我感觉这个 transaction 应该安全”，而要明确：

- 使用哪个隔离级别；
- 是否有 explicit lock；
- 是否有 unique/check constraint；
- 冲突时如何处理。

---

# 16. Unique Constraint 本身就是强大的并发工具

例如用户名唯一：

错误方式：

```text
SELECT username exists?
如果没有
INSERT
```

两个并发请求可能都看到：

```text
不存在
```

然后都 INSERT。

真正的最后防线：

```sql
UNIQUE (username)
```

两个请求同时插，数据库只允许一个成功。

所以很多“分布式锁”需求先问：

> 数据库 UNIQUE / conditional UPDATE / transaction 能不能直接解决？

---

# 17. Retry 不是万能修复

看到 timeout 之后直接：

```text
retry 3 times
```

非常危险。

因为第一次可能已经成功，只是响应丢了。

正确问题顺序：

```text
这个操作重复执行安全吗？
↓
有没有 idempotency key / unique constraint？
↓
这个错误真的可重试吗？
↓
重试总预算是多少？
```

不可重试：

```text
400 参数错误
401/403 权限错误
明确的业务冲突
```

可能可重试：

```text
部分网络 timeout
502/503
serialization/deadlock（具体判断）
429（遵守服务端限流信息）
```

---

# 18. 多层重试为什么会放大故障

假设：

```text
Client retry 3
Gateway retry 3
Service retry 3
SDK retry 3
```

最坏调用次数可能接近：

```text
3 × 3 × 3 × 3 = 81
```

原本一个下游故障，变成重试风暴。

所以重试要有明确 owner。

---

# 19. Webhook 为什么天然需要幂等

第三方系统通常会认为：

```text
没有收到 2xx
→ 我不知道你有没有处理
→ 我重发
```

于是 duplicate delivery 是正常行为，不是异常攻击才会发生。

常见设计：

```text
(provider, provider_event_id)
UNIQUE
```

处理：

```text
验证签名
↓
尝试 INSERT event
↓
首次 -> 应用业务变化
重复 -> 返回已经处理结果
```

不要用进程内 `set()` 充当生产幂等记录。

---

# 20. Transaction + Outbox 为什么会一起出现

业务操作：

```text
关闭工单
同时告诉其他消费者 ticket.closed
```

错误双写：

```text
UPDATE PostgreSQL ✅
PUBLISH Redis ❌
```

或者：

```text
PUBLISH ✅
UPDATE PostgreSQL ❌
```

两个系统无法被普通本地 transaction 一起原子提交。

Transactional Outbox 的方向：

```text
同一个 PostgreSQL Transaction：

UPDATE ticket
INSERT outbox_event
COMMIT
```

之后再由 Publisher 异步发布。

第 9 课会展开。

---

# 21. 三个必须会画的失败窗口

## 场景 A：COMMIT 前宕机

```text
BEGIN
INSERT
💥
```

结果：

```text
没有提交
```

重试通常可以重新做。

## 场景 B：COMMIT 后、Response 前宕机

```text
COMMIT ✅
💥
```

结果：

```text
业务已成功
客户端却以为失败
```

需要幂等。

## 场景 C：两个相同请求同时第一次到达

```text
A: key 不存在
B: key 不存在
```

如果只是先查再写，仍可能重复。

需要：

```text
数据库 UNIQUE / 原子 insert / transaction
```

来解决并发竞争。

---

# 22. 生产边界：transaction 也不是一切

事务不能替你解决：

- 跨系统原子提交；
- 外部 API 已经执行后的补偿；
- 整个服务不可用；
- 数据库备份；
- 长时间业务流程；
- 消息重复；
- 用户操作本身的业务语义。

长业务流程可能需要：

```text
state machine
outbox
saga / compensation
```

但不要没遇到问题就先上这些词。

---

# 23. 本仓库应该怎么练

使用：

```text
exercises/sql-postgres/
exercises/reliability-labs/
```

建议亲手证明：

### 实验 1：Constraint 与并发

两个并发 INSERT 同一个唯一 key，观察只有一个成功。

### 实验 2：Optimistic Lock

两个“客户端”都读取 version=1。

A 先更新成功，B 使用旧 version 更新，确认 B 影响 0 行。

### 实验 3：COMMIT 后响应丢失

模拟：

```text
数据库写成功
但是函数在返回前抛异常
```

然后使用相同 idempotency key 重试，证明没有第二条业务记录。

### 实验 4：Deadlock / lock timeout

在两个 session 以相反顺序锁两行，观察 PostgreSQL 如何处理。

只在本地实验库运行。

---

# 24. 关闭文档复述

1. Transaction 真正保护的范围是什么？
2. 为什么数据库 COMMIT 和客户端收到 200/201 是两个时刻？
3. 为什么 timeout 后盲目重试可能创建重复数据？
4. Idempotency Key 保护的是响应还是业务副作用？
5. 为什么幂等记录不能只存在进程内存？
6. request hash 解决什么问题？
7. Lost Update 是怎样发生的？
8. Optimistic Lock 为什么需要 version 条件？
9. `FOR UPDATE` 为什么不能无限持有？
10. Deadlock 为什么不代表数据库产品坏了？
11. Unique Constraint 为什么可以替代一部分“先查再锁”的设计？
12. 为什么外部 API/邮件不应该被想象成能跟 PostgreSQL transaction 一起 rollback？
13. Transactional Outbox 解决的双写窗口是什么？

如果能把“提交后响应丢失”的全过程自己画出来，你已经抓住后端可靠性最重要的核心之一。
