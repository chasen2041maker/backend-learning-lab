# 第 8 课：并发、goroutine、async、timeout、cancel 和 retry

这一课最容易被一堆词绕晕：

```text
concurrency
parallelism
goroutine
thread
async/await
channel
mutex
timeout
deadline
cancel
retry
```

先不要背 API。

先解决一个核心问题：

> **当一个服务同时处理很多事情时，怎样让它们高效推进，又不把自己和下游压垮？**

---

# 1. Concurrency 和 Parallelism 不是一回事

## Concurrency：并发

并发强调：

> 多个任务在同一时间段内都在推进。

例如一个 CPU 核心：

```text
Task A 执行一点
切换
Task B 执行一点
切换
Task C 执行一点
```

宏观上三个任务都在进行。

## Parallelism：并行

并行强调：

> 多个任务真的在同一个时刻执行。

例如多核 CPU：

```text
Core 1 -> Task A
Core 2 -> Task B
```

所以：

```text
并发 != 必然并行
```

一个并发程序可能只在一个核上交替执行，也可能被 runtime 调度到多个核上并行。

---

# 2. Goroutine 到底是什么

Go 里：

```go
go doWork()
```

会启动一个 goroutine。

可以先理解成：

> **由 Go runtime 管理和调度的轻量执行单元。**

它不是操作系统 thread 的简单别名。

Go runtime 会把大量 goroutine 调度到较少的 OS threads 上运行。

简化：

```text
Goroutine A ┐
Goroutine B ├─ Go Scheduler -> OS Threads -> CPU
Goroutine C ┘
```

所以 goroutine 是 Go 用来表达并发的基本工具之一。

但：

```text
goroutine 本身不是“并发这个概念”
```

更准确：

> goroutine 是 Go 提供的并发执行机制；一个程序可以通过多个 goroutine 让多个任务并发推进。

---

# 3. 为什么 goroutine 比“每个任务一个 OS thread”更适合很多服务

OS thread 通常有更高创建/调度成本和更大的 stack 起点。

Goroutine：

- 初始 stack 小；
- runtime 管理；
- 可以大量创建；
- 调度由 Go runtime 参与。

这让 Go 很适合：

```text
大量网络 I/O
大量 HTTP connections
大量独立请求
```

但不要推导成：

```text
goroutine 很轻
→ 启动 100 万个一定没问题
```

每个 goroutine 仍然占资源，而且它们会共同消耗：

- memory；
- CPU；
- file descriptors；
- DB connections；
- Redis connections；
- downstream QPS。

---

# 4. 并发为什么特别适合 I/O 等待

一个 HTTP 请求可能：

```text
CPU 计算 1ms
等待数据库 20ms
CPU 处理 1ms
等待下游 HTTP 100ms
```

大部分时间不是 CPU 真正在计算，而是在等 I/O。

如果一个任务等待时，另一个任务可以运行：

```text
CPU 不必空着
```

这就是网络服务中并发非常重要的原因。

---

# 5. CPU-bound 和 I/O-bound 要分开

## I/O-bound

大量时间等待：

- 网络；
- 数据库；
- 文件；
- Redis；
- 外部 API。

并发通常可以提高资源利用率。

## CPU-bound

大量时间真的在计算：

- 图像编码；
- 大规模压缩；
- 密集数学计算。

这时增加并发不一定变快，甚至可能因为调度竞争更慢。

需要考虑：

- 多核并行；
- worker process；
- 专门计算服务；
- GPU；
- batch。

---

# 6. Python async/await 又是什么

Python asyncio 的核心通常是 event loop。

简化：

```text
Task A -> 遇到 await I/O -> 暂停
                              ↓
Event Loop -> 运行 Task B
                              ↓
Task A 的 I/O 完成 -> 以后继续
```

例如：

```python
result = await client.fetch()
```

`await` 的意义不是：

```text
自动创建一个 CPU thread
```

而是：

> 当前 coroutine 等待一个可异步等待的操作时，把控制权交还 event loop，让别的 coroutine 推进。

---

# 7. 在 async 函数里调用阻塞函数会怎样

例如：

```python
async def handler():
    time.sleep(10)
```

虽然函数写了 `async`，但 `time.sleep` 是阻塞的。

结果：

```text
event loop 被占住
其他 coroutine 也可能无法推进
```

所以：

```text
async 语法 != 所有操作自动非阻塞
```

要使用真正的 async I/O 库，或把必须的 blocking work 放到合适 executor/thread/process 边界。

---

# 8. Goroutine 和 async 的共同问题

两种模型不同，但都必须回答：

```text
同时最多运行多少？
依赖最多能承受多少？
请求什么时候必须取消？
一个任务卡死会不会拖住所有资源？
```

也就是说：

> 并发机制只是让多个任务能推进；容量控制仍然是你的责任。

---

# 9. “启动多少 goroutine 都行”为什么危险

假设：

```text
10000 个输入
```

直接：

```go
for _, item := range items {
    go callDatabase(item)
}
```

数据库连接池只有：

```text
20 connections
```

于是：

```text
20 个执行
9980 个排队/等待
```

它们仍然占内存、deadline、调度和上下文。

下游也可能被瞬间打爆。

所以需要：

```text
bounded concurrency
```

---

# 10. Worker Pool 是什么

典型模型：

```text
Jobs Channel
   |
   +-> Worker 1
   +-> Worker 2
   +-> Worker 3
```

例如：

```go
func worker(jobs <-chan Job, results chan<- Result) {
    for job := range jobs {
        results <- process(job)
    }
}
```

这里：

```text
worker 数量
```

就是一个并发上限。

不是任务多少就启动多少 worker。

---

# 11. Channel 是什么

Go channel 可以理解成：

> goroutine 之间传递值并进行同步的一种机制。

例如：

```go
ch := make(chan int)
go func() {
    ch <- 42
}()

value := <-ch
```

数据流：

```text
Goroutine A
   |
   | 42
   v
 channel
   |
   v
Goroutine B
```

Channel 不是“所有共享状态的替代品”。

有时：

```text
mutex + shared data
```

反而更清晰。

---

# 12. Buffered 和 Unbuffered Channel

## Unbuffered

```go
make(chan int)
```

发送通常需要等到接收方准备好：

```text
sender <-> receiver rendezvous
```

## Buffered

```go
make(chan int, 10)
```

可以暂时积累最多 10 个值。

但 buffer 不是无限队列。

满了以后发送仍会阻塞。

Buffer 的意义应该来自：

- burst；
- producer/consumer speed；
- memory budget；
- backpressure。

不是“为了不阻塞就设一个超大数字”。

---

# 13. Close(channel) 表示什么

```go
close(ch)
```

表示：

> 不会再有新的值发送进这个 channel。

它不是：

```text
清空 channel
```

buffer 中已经存在的值仍然可以被 range 读完：

```go
for v := range ch {
    fmt.Println(v)
}
```

常见规则：

> 通常由发送方/拥有“发送结束”语义的一方负责 close。

不要让多个接收方随便 close 一个仍可能有人发送的 channel。

---

# 14. Mutex 是什么

多个 goroutine 共享：

```go
map[string]int
```

同时读写可能产生 data race，甚至直接导致运行时错误。

Mutex：

```go
mu.Lock()
// 修改共享状态
mu.Unlock()
```

表示同一临界区一次只允许一个执行者进入。

但锁范围应该小。

错误：

```go
mu.Lock()
callExternalAPI() // 等 20 秒
mu.Unlock()
```

所有竞争者都会一起等。

---

# 15. Data Race 和业务 Race 不完全一样

## Data Race

两个 goroutine 并发访问同一内存位置，至少一个写，并且缺少正确同步。

Go 可以使用：

```powershell
go test -race ./...
```

检测大量 data race。

## 业务 Race

即使内存访问完全线程安全，业务仍可能错误。

例如：

```text
A 查询余额=100
B 查询余额=100
A 扣 80
B 扣 80
```

代码可能没有 Go data race，因为数据库访问本身是线程安全的。

但业务产生了 lost update / overspend。

这需要 transaction/lock/version，而不是 Go mutex。

---

# 16. Context 是 Go 后端的关键基础

HTTP 请求自带：

```go
r.Context()
```

Context 主要传播 request-scoped：

- cancellation；
- deadline；
- 少量 metadata，例如 request ID / Principal。

典型：

```text
HTTP Request ctx
      ↓
Handler
      ↓
Service
      ↓
Repository
      ↓
DB / HTTP client
```

如果客户端断开或 deadline 到期，下游应该尽量停止不再需要的工作。

---

# 17. Timeout / Deadline / Cancel 有什么区别

## Timeout

相对时间：

```text
最多等 2 秒
```

Go：

```go
ctx, cancel := context.WithTimeout(parent, 2*time.Second)
defer cancel()
```

## Deadline

绝对时间点：

```text
最晚 12:00:02 结束
```

整个请求通常应该有一个总 deadline。

## Cancel

显式告诉下游：

```text
这个结果已经不需要了
停止工作
```

Cancel 并不强行“杀死 goroutine”。

下游代码必须：

- 使用支持 context 的 API；
- 或主动检查 `ctx.Done()`。

---

# 18. 为什么每个下游都要 timeout

请求：

```text
Client
→ API
→ Redis
→ Database
→ External API
```

如果 External API 永不返回，API 也无限等待：

```text
connection
memory
goroutine
```

都会被长期占用。

最终形成资源耗尽。

所以：

> timeout 是资源边界，不只是“用户不想等太久”。

---

# 19. 总 Deadline 和单次 Timeout 不一样

假设整个 HTTP 请求最多：

```text
3 秒
```

但你依次调用三个下游：

```text
A timeout 2s
B timeout 2s
C timeout 2s
```

如果每次都重新获得 2 秒：

```text
总时间可能 6 秒以上
```

更合理：

```text
整个请求 deadline = 3s
每个子调用使用剩余预算中的一部分
```

这叫 deadline propagation / budget。

---

# 20. 排队也消耗 Deadline

一个任务可能不是正在运行，而是在等 semaphore / connection pool：

```text
request deadline = 2s
排队 1.8s
真正执行只剩 0.2s
```

所以容量限制和 deadline 必须一起设计。

不要只给“开始执行后的 HTTP client”设 timeout，却让前面的队列无限等。

---

# 21. Backpressure 是什么

Producer 比 Consumer 快：

```text
Producer 10000/s
Consumer 100/s
```

如果无限缓存：

```text
queue
queue
queue
memory 爆炸
```

Backpressure 的核心：

> 下游处理不过来时，上游必须感知并减速、拒绝、排队有界化或降级。

形式可能是：

- bounded channel；
- semaphore；
- HTTP 429/503；
- queue max size；
- rate limit。

---

# 22. Retry 是并发系统里最容易放大的机制

失败：

```text
timeout
```

第一反应不能是：

```text
再发一次
```

先问：

```text
第一次真的没成功吗？
操作幂等吗？
失败是暂时性吗？
还剩多少 deadline？
```

---

# 23. Exponential Backoff 和 Jitter

如果 1000 个客户端同时失败，然后都：

```text
1 秒后重试
```

1 秒后又形成 1000 请求尖峰。

Backoff：

```text
1s
2s
4s
8s
```

Jitter：

```text
在等待时间上加随机扰动
```

让重试错开。

例如概念上：

```text
2s + random(0..500ms)
```

---

# 24. 哪些错误不要重试

通常不应该自动重试：

```text
400 invalid input
401 unauthenticated
403 forbidden
明确业务冲突
```

可能适合有限重试：

```text
temporary network timeout
502
503
429（尊重 Retry-After）
某些数据库 serialization/deadlock
```

真正判断要看接口契约和幂等性。

---

# 25. 多层 Retry 会指数放大

```text
Client retry 3
Gateway retry 3
Service retry 3
SDK retry 3
```

最坏：

```text
81 次调用
```

因此系统应该明确：

```text
谁负责 retry？
总预算多少？
```

---

# 26. Partial Failure：并发调用不是“全成或全败”

同时调用：

```text
天气 API
库存 API
推荐 API
```

可能：

```text
天气成功
库存 timeout
推荐成功
```

系统必须定义：

```text
库存是关键依赖吗？
能返回部分结果吗？
还是整个请求失败？
```

这叫 failure policy。

不要等代码写完后才决定。

---

# 27. Graceful Shutdown 和并发有什么关系

服务器收到退出信号：

```text
不要立刻 kill 所有请求
```

常见流程：

```text
停止接收新请求
↓
给正在执行的请求一个结束窗口
↓
cancel 超时任务
↓
关闭数据库/Redis连接等资源
↓
退出
```

Go 的 `http.Server.Shutdown(ctx)` 就是这一类机制。

---

# 28. 本仓库怎么练

### Go 最小实验

写一个 worker pool：

```text
10 jobs
3 workers
```

验证：

- 同时最多约 3 个任务处理；
- jobs 关闭后 workers 正常退出；
- results 最终关闭；
- 不出现 goroutine leak。

### Go race 实验

用多个 goroutine 写一个 map：

```powershell
go test -race ./...
```

观察 data race，然后用 mutex 或重构 ownership 修复。

### Timeout 实验

调用一个故意 sleep 的 fake dependency：

```text
dependency 5s
request deadline 1s
```

验证服务在约 1s 左右结束，而不是 5s。

### Python reliability lab

运行：

```powershell
python -m unittest exercises/reliability-labs/tests/test_patterns.py -v
```

重点阅读 `concurrency_timeout.py` 的：

- max concurrency；
- per-call timeout；
- total timeout。

---

# 29. 常见误区

## goroutine = thread

不准确。

Goroutine 由 Go runtime 调度，并映射到 OS threads。

## goroutine = 并发

不准确。

Goroutine 是实现 Go 并发的一种执行单元。

## 并发 = 并行

错误。

并发强调任务重叠推进；并行强调真正同时执行。

## channel 比 mutex 高级

错误。

两者解决不同同步/ownership 模型。

## `async def` 里的代码自动不阻塞

错误。

Blocking call 仍会阻塞 event loop。

## timeout 只是提升用户体验

错误。

它更重要的作用是限制资源被无限占用。

## retry 能提升可靠性

不完整。

没有幂等、backoff、budget 的 retry 可能让故障更严重。

---

# 30. 关闭文档复述

1. Concurrency 和 Parallelism 有什么区别？
2. Goroutine 是什么？为什么不能简单叫 OS thread？
3. 为什么 goroutine 很轻仍然不能无限创建？
4. I/O-bound 为什么适合并发？
5. Python `await` 到底在让出什么？
6. 为什么 async 函数里调用 blocking library 仍然会卡 event loop？
7. Worker pool 的并发上限解决什么风险？
8. Unbuffered 和 buffered channel 的关键区别是什么？
9. 为什么 channel close 通常由发送生命周期 owner 负责？
10. Data race 和数据库 lost update 有什么区别？
11. `context.Context` 应该传播什么，不应该拿来做什么？
12. Timeout、Deadline、Cancel 分别是什么？
13. 为什么排队时间也必须算进总 deadline？
14. Backpressure 的本质是什么？
15. 为什么 retry 必须和 idempotency 一起思考？
16. 多层 retry 为什么可能形成放大？
17. Graceful shutdown 为什么不是直接 `os.Exit`？

如果这些能讲清楚，你再看 goroutine/channel 代码，就不会只是在背语法。
