# Redis 缓存与 Streams 实验

先启动 `exercises/infrastructure` 的 Redis：

```powershell
python -m pip install -r requirements.txt
python cache_demo.py
python stream_demo.py produce
python stream_demo.py consume
```

## `cache_demo.py`

观察：

1. 第一次 cache miss，从模拟事实源加载；
2. 第二次 cache hit；
3. 删除缓存后仍可从事实源恢复；
4. 不存在数据使用短 TTL 负缓存；
5. 所有 Key 都有 TTL。

## `stream_demo.py`

生产一条完整 `ticket.closed` Envelope，再用 Consumer Group 读取、演示幂等标记并 ACK。脚本中的 Redis 幂等标记只用于观察重复消息；生产业务必须把 `processed_events` 与业务写入放在同一个 PostgreSQL 事务中，不能用这个演示 Key 代替事实库事务。

按下面顺序完成一次可重复的宕机恢复实验：

```powershell
python stream_demo.py produce
python stream_demo.py consume-crash  # 模拟副作用完成、ACK 前宕机
python stream_demo.py pending        # 对应 XPENDING
python stream_demo.py reclaim        # 对应 XAUTOCLAIM，接管并 ACK
python stream_demo.py pending        # pending 应回到 0
```

`reclaim` 为了让本地实验立即完成，把 `min_idle_time` 设为 0。生产环境必须使用大于正常处理时长的阈值，避免两个消费者同时处理仍在运行的任务。观察恢复消费者如何用同一 `event_id` 跳过重复副作用。

这些脚本只用于本地理解协议，不是生产级事件框架。
