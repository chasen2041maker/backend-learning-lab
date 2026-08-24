# Redis 实验：先声明角色，再讨论 Key、TTL 和 Streams

Redis 很容易学成一组命令：

```text
GET / SET / EXPIRE / XADD / XREADGROUP / ACK
```

这个目录刻意反过来：**先说 Redis 在当前场景扮演什么角色，再运行命令。**

本仓库常见角色：

```text
cache
session
rate limit
coordination
stream transport
```

不同角色的“Redis 丢了怎么办”完全不同。

先阅读 [`lessons/07-redis.md`](../../lessons/07-redis.md)；Streams/异步再结合 [`lessons/09-streams-outbox.md`](../../lessons/09-streams-outbox.md)。

## 启动

先启动本地 Redis：

```powershell
cd exercises\infrastructure
docker compose up -d redis
docker compose exec redis redis-cli ping
```

然后在 `exercises/redis-lab` 按当前环境安装依赖并运行脚本。

## 1. `cache_demo.py`：证明 Cache 不是事实源

观察顺序：

```text
第一次读取
→ cache miss
→ 从模拟事实源读取
→ 回填 Redis

第二次读取
→ cache hit
```

然后删除 Key：

```text
cache disappears
→ 再次从事实源恢复
```

这一步最重要，因为它证明：

> **缓存是派生状态，丢失时应有重建路径。**

实验还演示：

- 不存在对象的短 TTL negative cache；
- Key 应有明确 TTL，而不是无界永久堆积。

## 2. TTL 解决什么、不解决什么

TTL 解决：

```text
数据最终自动过期
```

但不保证：

```text
数据库刚更新
→ Redis 这一毫秒立刻一致
```

所以更新事实后仍要思考 invalidation/update policy。

如果只说“TTL=60s，所以一致”，是不准确的。

## 3. 穿透、击穿、雪崩要放进真实流量理解

```text
穿透：大量请求查询本来就不存在的 key
击穿：一个极热点 key 失效，大量请求同时回源
雪崩：大量 key 同时失效/Redis 故障，大面积回源
```

它们共同的问题不是名词，而是：

```text
下游事实源能不能承受突然放大的流量？
```

negative cache、singleflight/锁、TTL jitter、限流等都是针对具体流量形状的手段，不是固定套餐。

## 4. `stream_demo.py`：把消息生命周期跑出来

生产：

```powershell
python stream_demo.py produce
```

正常消费：

```powershell
python stream_demo.py consume
```

链路：

```text
XADD event
→ Consumer Group delivery
→ validate envelope/version
→ business/idempotency
→ ACK
```

重点不是“Redis 能当消息队列”，而是 ACK 的时机决定故障语义。

## 5. 亲手跑 ACK 前崩溃

按顺序：

```powershell
python stream_demo.py produce
python stream_demo.py consume-crash
python stream_demo.py pending
python stream_demo.py reclaim
python stream_demo.py pending
```

你应该观察到：

```text
消息已经投递
但没有 ACK
→ 进入 Pending
→ 新消费者 reclaim
→ 再处理/幂等跳过
→ ACK
→ Pending 回到 0
```

这就是 at-least-once 世界中的典型恢复路径。

## 6. 为什么 Consumer 仍然必须幂等

最危险窗口：

```text
业务副作用成功
↓
ACK 前进程崩溃
```

消息以后会再次投递。

所以：

```text
delivery may repeat
→ business effect must not repeat
```

脚本里的 Redis processed marker 只是教学观察手段。生产业务如果最终事实写 PostgreSQL，通常需要：

```text
processed_events
+
business update
```

处于同一个数据库事务中。

不能用一个容易丢失的 demo Redis Key 假装获得了业务 exactly-once。

## 7. `min_idle_time=0` 为什么只能用于本地实验

为了让你不用等待，`reclaim` 可把 idle threshold 设成 0。

真实系统如果这么做：

```text
Worker A 还在正常处理
↓
Worker B 立刻认为它失联并 reclaim
↓
两个 Worker 同时处理
```

生产阈值必须大于正常处理时长，并结合 heartbeat/lease、任务幂等和监控设计。

## 8. DLQ 不是“错误垃圾桶”

非法 Envelope / 不支持 version 可以进入：

```text
lab:events:dlq
```

但生产 DLQ 必须回答：

```text
谁监控？
什么时候报警？
如何诊断？
修复后如何 replay？
replay 会不会重复副作用？
```

只把消息丢进去不处理，不叫完整恢复方案。

## 9. Redis unavailable 时先决定策略

不同角色：

```text
cache unavailable
→ 可能有界回源/降级

session unavailable
→ 可能无法确认登录状态，倾向 fail closed

rate limit unavailable
→ fail-open 还是 fail-closed 取决于风险

stream unavailable
→ producer/consumer 要明确失败、缓冲或重试语义
```

所以不要写一个统一：

```text
except RedisError: pass
```

## 10. 完成证据

至少记录：

```text
Cache miss/hit：
删除 cache 后如何恢复：
negative cache 的原因：
一次 Pending/reclaim：
ACK 前 crash 会怎样：
重复消息为什么不重复副作用：
当前 Redis 角色：
Redis 故障策略：
```

如果能运行 `redis-cli` 命令，却说不清 Redis 在当前链路是事实、缓存还是 transport，这个实验还没有真正完成。
