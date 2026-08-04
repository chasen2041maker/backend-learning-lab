# 第 8 课：异步、并发、超时、取消和重试

## 并发不是更快的魔法

并发适合等待多个独立 I/O：数据库、HTTP、Redis。CPU 密集任务不会因为 Python asyncio 自动变快，过多 goroutine/协程也会压垮下游。

## Python

```python
async with asyncio.timeout(2.0):
    result = await client.fetch()
```

`await` 只表示当前协程愿意让出执行权。阻塞库放进异步函数仍会阻塞事件循环。

## Go

```go
ctx, cancel := context.WithTimeout(parent, 2*time.Second)
defer cancel()
result, err := client.Fetch(ctx)
```

下游调用必须真正监听 `ctx.Done()`，否则上游取消了，它仍可能继续消耗资源。

## 有限并发

一次请求需要查询 100 个股票，不应直接启动 100 个无限制调用。使用 semaphore、worker pool 或批量接口，并让并发上限来自容量验证。

## 重试条件

只对暂时性错误重试，例如部分 429、502、503、网络超时。参数错误和权限错误不应重试。

可靠重试需要：

- 操作幂等；
- 指数退避；
- 随机抖动；
- 最大次数或总 deadline；
- 可观测的最终失败；
- 避免每一层都重试造成放大。

## 练习

并发调用三个假下游：一个成功、一个 500、一个超时。程序必须在总 deadline 内结束，并清楚区分部分成功、可重试失败和取消。
