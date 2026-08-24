# 第 7 课：Redis——为什么快、适合做什么、什么时候反而不该用

很多教程一上来就教：

```text
SET
GET
EXPIRE
```

但真正重要的问题是：

> **Redis 在这个系统里到底扮演什么角色？它丢了以后，业务应该发生什么？**

如果这个问题答不出来，就不应该先写 Redis 代码。

---

# 1. Redis 是什么

可以先把 Redis 理解成：

> 一个通过网络访问的、主要以内存为工作数据集、支持多种数据结构和 TTL 的数据服务器。

典型链路：

```text
Go / Python App
      |
      | TCP
      v
Redis Server
      |
      v
key -> value / hash / set / stream ...
```

Redis 是独立进程，不是你程序里的 `map`。

所以它也有：

- 网络连接；
- command timeout；
- connection pool；
- 内存上限；
- 重启；
- 持久化配置；
- 主从/故障切换等运行问题。

---

# 2. Redis 为什么通常很快

简化理解：

```text
主要操作内存
+
数据结构和命令相对直接
+
避免每次都做复杂磁盘查询
```

但不要把：

```text
Redis 在内存里
```

错误理解成：

```text
Redis 永远比数据库快
Redis 可以替代 PostgreSQL
```

业务系统选择存储，不只看单次延迟，还看：

- 数据能不能丢；
- 事务语义；
- 查询能力；
- 恢复；
- 审计；
- 容量；
- 一致性。

---

# 3. 每次用 Redis 前先给它贴角色标签

## 角色 A：Cache

```text
PostgreSQL = 事实源
Redis = 可重建加速副本
```

Redis 丢了：

```text
系统变慢
但业务事实仍在
```

这是最容易理解的 Redis 场景。

## 角色 B：Session / 短期状态

例如：

```text
session_id -> user_id
验证码
临时登录状态
```

这种数据可以有 TTL，但是否允许丢失取决于业务。

Session Redis 丢失可能意味着：

```text
用户全部需要重新登录
```

这不是“完全没影响”，但通常比订单数据丢失更可接受。

## 角色 C：Rate Limit / Counter

例如：

```text
user:42:login_attempts -> 4
```

Redis 的原子计数和 TTL 很适合很多限流实现。

## 角色 D：Coordination

例如：

- 临时锁；
- leader/lease；
- 去重窗口；
- 在线连接目录。

但协调问题最容易被误用，后面会讲锁边界。

## 角色 E：Streams / Message Transport

Redis Streams 可以承担：

```text
producer
→ stream
→ consumer group
→ pending / ack
```

这已经不是普通缓存，而是异步消息传递角色。

第 9 课展开。

---

# 4. 什么东西不应该只放 Redis

如果 Redis 被全部清空以后，这些业务事实无法恢复，就要非常谨慎：

- 订单最终状态；
- 支付结果；
- 用户余额；
- 工单最终状态；
- 审计记录；
- 唯一保存的用户内容。

不是说 Redis 技术上“不能持久化”。

而是要问：

> **你真的愿意把这类事实的持久性、恢复、事务和审计全部押在当前 Redis 架构上吗？**

对这个学习仓库，默认 PostgreSQL 保存业务事实，Redis 承担可重建或运行时角色。

---

# 5. Cache Aside 是什么

最经典读流程：

```text
Request
  ↓
GET Redis
  ├─ hit -> 返回
  │
  └─ miss
      ↓
    SELECT PostgreSQL
      ↓
    SET Redis + TTL
      ↓
    返回
```

伪代码：

```text
value = cache.get(key)
if value exists:
    return value

value = db.load(id)
cache.set(key, value, ttl)
return value
```

Cache Aside 的关键不是代码，而是：

> Redis 只是派生副本，数据库仍是事实源。

---

# 6. 为什么缓存必须有 TTL

如果永不过期：

```text
数据库已经变化
Redis 仍然保留旧值
```

TTL 给旧数据一个自动退出的上限。

例如：

```text
SET ticket:123 ... EX 60
```

表示：

```text
最多缓存约 60 秒
```

TTL 不是一致性保证。

它只是：

```text
最终会自动失效的一层控制
```

---

# 7. 写数据库后为什么常见“删除缓存”

一种常见做法：

```text
UPDATE PostgreSQL
↓
DEL Redis cache key
```

下一次读：

```text
cache miss
→ 重新从数据库加载新值
```

为什么不是简单：

```text
UPDATE DB
SET cache=new value
```

因为并发时两个更新/读取可能交错，直接“同步更新缓存”也会产生竞态。

但要明确：

> “先写库再删缓存”也不是数学意义上的强一致。

业务需要多强的一致性，要根据读写模式设计。

---

# 8. 三个经常听到的缓存风险

## Cache Penetration：穿透

大量请求查询根本不存在的数据：

```text
Redis miss
→ DB miss
Redis miss
→ DB miss
...
```

缓存永远帮不上忙。

可能处理：

- 负缓存；
- 输入/ID 边界；
- 某些场景 Bloom Filter。

不要看到“穿透”就自动上 Bloom Filter。

## Cache Breakdown / Hot Key Expiry：击穿

一个非常热门 key 刚好过期：

```text
1000 requests
同时 miss
同时打 DB
```

可能处理：

- singleflight；
- 小范围互斥重建；
- 提前刷新；
- 热点不过期 + 主动刷新等。

## Cache Avalanche：雪崩

大量 key 在同一时间过期，或者 Redis 整体不可用：

```text
大量流量突然回源数据库
```

可能处理：

- TTL jitter；
- 容量保护；
- 限流；
- 降级；
- 数据库本身具备承受合理回源的能力。

---

# 9. TTL Jitter 是什么

假设 100 万个 key 都设置：

```text
TTL = 3600s
```

如果它们又差不多同时写入，就可能差不多同时过期。

可以设置：

```text
3600 + random(0..300)
```

让过期时间打散。

这叫 jitter。

但 jitter 不是解决所有缓存故障的魔法，它只是在缓解同步过期。

---

# 10. Redis 数据结构不是“类型越多越高级”

常见：

```text
String
Hash
List
Set
Sorted Set
Stream
```

学习时优先问语义。

### String

适合：

```text
cache value
counter
simple token state
```

### Hash

一个 key 下多个 field：

```text
user:42
  name -> Alice
  role -> admin
```

### Set

无序唯一成员：

```text
online_users
permissions
```

### Sorted Set

成员 + score：

```text
leaderboard
延迟队列的一些实现
```

### Stream

追加消息日志 + consumer group。

不要因为 Redis 有数据结构，就把它当关系数据库做复杂事实建模。

---

# 11. 原子命令为什么重要

危险：

```text
GET count
count++
SET count
```

两个客户端并发：

```text
A GET 5
B GET 5
A SET 6
B SET 6
```

本应变成 7，结果只有 6。

Redis 有：

```text
INCR
```

服务器端原子执行：

```text
INCR count
```

这说明一个通用后端原则：

> 尽量把竞争条件交给拥有状态的一方用原子操作解决，而不是客户端“先读再写”。

数据库的 `UPDATE ... SET count=count+1`、UNIQUE constraint 也是同一类思维。

---

# 12. Redis Transaction 和数据库 Transaction 不要混为一谈

Redis 有：

```text
MULTI / EXEC
```

也有 Lua script 等原子执行能力。

但它和 PostgreSQL 的复杂事务语义、约束、隔离并不是同一个东西。

不要看到“Redis transaction”这个词，就认为：

```text
它等价于关系数据库 transaction
```

具体语义必须看命令和故障模型。

---

# 13. Redis 持久化：RDB / AOF 是什么层面的问题

Redis 可以配置持久化，例如：

```text
RDB snapshot
AOF
```

这意味着 Redis 不一定“重启就全部丢”。

但持久化策略会带来：

- 性能；
- 数据丢失窗口；
- 文件恢复；
- rewrite；
- 运维复杂度。

所以本课程中说“Redis 数据应该可重建”，不是因为 Redis 完全不能持久化，而是为了先建立清晰的事实边界。

---

# 14. Eviction：内存满了怎么办

Redis 有最大内存策略。

如果达到：

```text
maxmemory
```

可能：

- 拒绝某些写；
- 淘汰有 TTL 的 key；
- LRU/LFU 类淘汰；
- 按配置处理。

因此缓存设计必须知道：

```text
key 可能提前消失
```

如果一个业务流程依赖：

> 这个 key 绝对不能没

那你必须重新审视它是不是应该只存在 Redis。

---

# 15. Redis Connection Pool 也会耗尽

应用大量请求：

```text
Request 1 -> Redis
Request 2 -> Redis
...
```

通常会复用连接池。

如果 Redis 变慢：

```text
命令占住连接
↓
pool 等待越来越多
↓
整个 API 开始排队
```

所以要有：

- connect timeout；
- command timeout；
- pool size；
- pool wait timeout；
- metrics。

“Redis 很快”不是取消 timeout 的理由。

---

# 16. Redis 挂了，应该 fail 还是 degrade

取决于角色。

### 如果只是缓存

可能：

```text
Redis unavailable
→ bypass cache
→ query PostgreSQL
```

但必须有回源容量保护，不能瞬间压垮 DB。

### 如果是 Session Store

可能：

```text
无法确认登录会话
→ 认证失败 / 服务降级
```

不能随便“Redis 挂了就默认用户登录成功”。

### 如果是 Rate Limiter

要根据安全风险选择：

```text
fail-open
or
fail-closed
```

例如安全敏感接口可能不能在限流器挂掉时完全无限制开放。

### 如果是 Stream

异步任务可能暂停积压，但业务事实应该仍在 PostgreSQL/Outbox 中等待恢复。

---

# 17. Redis Lock 为什么比 `SET NX PX` 复杂

最小锁：

```text
SET lock:key random-owner NX PX 5000
```

看起来：

```text
只有一个客户端能拿到
5 秒后自动过期
```

但真实问题：

```text
Worker A 拿锁
→ 卡住 8 秒
锁 5 秒过期
Worker B 拿到新锁
A 恢复继续写
```

现在：

```text
A 和 B 都可能认为自己可以操作
```

所以锁不仅是“谁拿到 key”，还涉及：

- owner token；
- 安全释放；
- expiry；
- renew；
- stale worker；
- fencing token；
- 下游事实源是否验证版本。

---

# 18. 错误释放锁的问题

错误：

```text
DEL lock:key
```

场景：

```text
A 的锁已经过期
B 已经拿到新锁
A 恢复后 DEL
```

A 可能把 B 的锁删掉。

因此释放至少需要：

```text
只有 value 仍然等于我的 owner token 才删除
```

通常通过原子 script 实现。

但更重要的问题仍然是：

> 这个需求是不是根本可以用数据库 unique / version / `FOR UPDATE` 更可靠地解决？

---

# 19. Fencing Token 是什么

即使有 lease，旧 worker 仍可能在过期以后恢复。

可以给每次所有权一个单调递增版本：

```text
Worker A token=41
Worker B token=42
```

事实库只允许：

```text
>= current fencing token
```

于是旧 A 拿着 41 回来写：

```text
拒绝
```

这叫 fencing。

第 9 课在长任务/Outbox 中继续用。

---

# 20. Session 为什么经常放 Redis

Session 典型：

```text
session_id -> user_id / auth state
TTL = 7 days
```

Redis 很适合：

- 按 key 读取；
- TTL；
- 多实例共享。

但要理解影响：

```text
Redis session 数据丢失
→ 用户可能全部掉登录
```

这可能是可接受故障，而不是“完全无损”。

---

# 21. Rate Limit 的核心不是“用 Redis”

真正问题：

```text
谁？
在什么时间窗口？
最多多少次？
超过以后怎么处理？
多个应用实例如何共享计数？
```

Redis 只是实现共享计数/时间窗口的一种工具。

算法可能包括：

- fixed window；
- sliding window；
- token bucket；
- leaky bucket。

先理解业务限制，再选实现。

---

# 22. Redis 和数据库一致性永远值得问

当同一个业务概念同时存在：

```text
PostgreSQL
和
Redis
```

就要问：

```text
谁是真相？
谁先写？
中间失败怎么办？
Redis 旧值最多能活多久？
缓存删除失败怎么办？
```

缓存不是免费性能，它增加了一份状态。

状态越多，一致性问题越多。

---

# 23. 本仓库实验

进入：

```powershell
cd exercises\redis-lab
```

建议至少观察：

## 实验 1：Cache Aside

```text
第一次查询 -> cache miss -> DB/source
第二次查询 -> cache hit
删除 key -> 再次回源
```

## 实验 2：TTL

设置短 TTL，观察 key 自动消失。

## 实验 3：Redis 整体清空

问：

```text
哪些业务事实还在？
哪些只是性能下降？
```

## 实验 4：并发计数

比较：

```text
GET + SET
```

与原子：

```text
INCR
```

## 实验 5：Streams

只先观察消息写入和读取，不急着把 Streams 当“Kafka 入门替代品”。

---

# 24. 常见误区

## Redis = Cache

不完整。

Redis 可以承担多种角色，但每次必须明确角色。

## Redis = 内存，所以不持久化

不准确。

Redis 有持久化能力，但这不自动让它适合所有业务事实。

## Redis 比 PostgreSQL 快，所以优先 Redis

错误。

存储选择不只看延迟。

## 分布式系统有并发，所以用 Redis Lock

错误。

先问数据库约束/事务/version 是否已经足够。

## Redis 挂了就直接查数据库，没有问题

不一定。

缓存雪崩可能把数据库压垮，需要容量和降级设计。

---

# 25. 关闭文档复述

1. Redis 和 Go `map` 的最大运行时区别是什么？
2. 为什么说使用 Redis 前必须先明确角色？
3. Cache Aside 的 source of truth 是谁？
4. TTL 能不能保证数据库和缓存强一致？
5. 穿透、击穿、雪崩分别发生什么？
6. 为什么 TTL jitter 有用？
7. `INCR` 比 `GET -> +1 -> SET` 解决了什么并发问题？
8. Redis 持久化存在，为什么课程仍建议核心业务事实放 PostgreSQL？
9. Redis connection pool 为什么也会形成瓶颈？
10. Cache Redis 挂了和 Session Redis 挂了，故障语义为什么不同？
11. `SET NX PX` 为什么不是完整分布式锁方案？
12. fencing token 防的是哪一类 stale worker？
13. 为什么“加缓存”其实是在系统里增加一份需要管理的状态？

如果这些能解释清楚，你再看 Redis 的具体命令会容易很多，因为你知道每条命令是在解决哪种业务角色的问题。
