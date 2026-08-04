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

生产一条 `ticket.closed`，再用 Consumer Group 读取、演示幂等标记并 ACK。脚本中的 Redis 幂等标记只用于观察重复消息；生产业务必须把 `processed_events` 与业务写入放在同一个 PostgreSQL 事务中，不能用这个演示 Key 代替事实库事务。

独立练习：在 ACK 前强制退出，查看 `XPENDING`；重新运行时使用 `XAUTOCLAIM` 接管超时消息。思考业务已经提交、ACK 尚未发生时，为什么仍需要 `event_id` 幂等。

这些脚本只用于本地理解协议，不是生产级事件框架。
