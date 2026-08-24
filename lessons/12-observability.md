# 第 12 课：日志、指标、Trace、健康检查与 SLO——系统出问题时你看什么

一个后端服务在本地运行时，你可以盯着终端看。

生产环境不行：

```text
几十个实例
成千上万请求
异步 Worker
数据库
Redis
外部 API
模型供应商
```

真正的问题是：

> **用户说“刚才很慢/失败了”，你怎么知道发生在哪里、影响多大、是不是还在发生、应该先处理什么？**

Observability（可观测性）就是让系统通过外部信号帮助你推断内部状态。

---

# 1. Log、Metric、Trace 分别解决什么

## Log：具体发生了什么

一条结构化日志：

```json
{
  "level": "error",
  "service": "ticket-api",
  "request_id": "req_123",
  "operation": "create_ticket",
  "error_code": "db_timeout",
  "duration_ms": 812
}
```

适合回答：

```text
这一件具体事情发生了什么？
```

## Metric：整体趋势怎样

例如：

```text
http_requests_total
http_request_duration_seconds
http_errors_total
```

适合回答：

```text
过去 10 分钟错误率是不是升高？
P95 延迟是不是恶化？
```

## Trace：一次调用跨组件经历什么

```text
Client
  ↓ 30ms
Gateway
  ↓ 20ms
Ticket Service
  ↓ 700ms
PostgreSQL
```

适合回答：

```text
这一整个请求 800ms，到底时间花在哪里？
```

所以：

```text
Log ≠ Metric ≠ Trace
```

它们互补。

---

# 2. 为什么“多打日志”不是可观测性

如果每个请求打印 500 行：

```text
enter function A
value x=...
leave function A
...
```

可能产生：

- 成本高；
- 噪声大；
- 隐私泄露；
- 搜索困难；
- 真正错误被淹没。

更重要的是建立：

```text
稳定字段
关联 ID
清晰错误码
关键状态变化
关键耗时
```

而不是输出越多越好。

---

# 3. Structured Logging 为什么比拼字符串更有用

差：

```text
error user 42 ticket abc db timeout after 812
```

更适合机器处理：

```json
{
  "level":"error",
  "user_id":"...",
  "ticket_id":"...",
  "error_code":"db_timeout",
  "duration_ms":812
}
```

字段可以被：

- 搜索；
- 聚合；
- Dashboard；
- Alert；
- 自动分析。

但敏感字段仍然不能因为“结构化”就随便记录。

---

# 4. 日志里应该有什么

常见基础字段：

```text
timestamp
level
service
env
version
operation
outcome
duration_ms
error_code
```

请求链常加：

```text
request_id
trace_id
```

异步链可能加：

```text
event_id
task_id
attempt
```

多租户系统可以记录非敏感 tenant identifier，但仍要考虑隐私和日志访问权限。

---

# 5. 日志里绝对不该随便放什么

高风险：

```text
password
JWT / Access Token
Refresh Token
API Key
JWT_SECRET
数据库密码
完整 Cookie
信用卡信息
用户隐私原文
未经控制的完整 Prompt / 文档内容
```

日志系统通常：

- 保存很久；
- 很多人能访问；
- 复制到多个平台。

所以“方便调试”不是泄露 Secret 的理由。

---

# 6. Request ID 是什么

一次入口请求生成：

```text
X-Request-ID: req_123
```

同一个服务内日志：

```text
req_123 request started
req_123 db query started
req_123 db timeout
req_123 response 503
```

你可以把一次请求串起来。

但：

```text
Request ID 本身不是 Trace
```

如果跨多个服务，需要更统一的 distributed tracing context。

---

# 7. Trace ID / Span 是什么

一条 Trace：

```text
Trace ID = T1

Span: Gateway request
  |
  +-- Span: Ticket Service
       |
       +-- Span: PostgreSQL query
       |
       +-- Span: Redis GET
```

每个 Span 通常记录：

- start/end；
- duration；
- operation；
- status；
- parent/child relationship；
- 少量 attributes。

这样可以看到完整 critical path。

---

# 8. Trace 不是“把所有参数都采集下来”

Trace 也有：

- 成本；
- 隐私；
- cardinality；
- sampling。

不要把完整 request body、Token、Prompt、数据库行无脑塞进 span attributes。

可观测性数据同样需要安全设计。

---

# 9. Metric 的核心是聚合

例如：

```text
http_requests_total{method="GET",route="/api/v1/tickets",status="200"}
```

随着请求增加：

```text
100
101
102
```

系统可以计算速率。

延迟通常用 histogram 等方式记录分布，而不是只存一个平均值。

---

# 10. 为什么 Average Latency 很容易骗人

10 个请求：

```text
9 个 = 50ms
1 个 = 5000ms
```

平均：

```text
545ms
```

它无法告诉你用户体验分布。

通常会看：

```text
P50
P95
P99
```

例如：

```text
P50 = 50ms
P95 = 200ms
P99 = 5s
```

这更能暴露 tail latency。

---

# 11. RED 是什么

对请求型服务，一个非常实用的起点：

```text
Rate
Errors
Duration
```

即：

```text
请求有多少？
失败多少？
有多慢？
```

如果一个 API 连这三类都没有，就很难快速判断用户影响。

---

# 12. Resource Metrics 也要看

除了用户请求，还要看资源：

```text
CPU
memory
file descriptors
DB pool in-use/waiting
Redis pool
 goroutine count
thread/task count
queue depth
```

例如错误率还没升，但：

```text
DB pool waiting rapidly increasing
```

可能已经预示即将故障。

---

# 13. Async 系统不能只看 HTTP RED

Worker 没有 HTTP 500，不代表健康。

异步系统要看：

```text
queue / stream backlog
oldest pending age
processed rate
failure rate
retry rate
DLQ count
Outbox unpublished age
lease expiry/reclaim
```

最关键常常不是：

```text
队列里有 1000 条
```

而是：

```text
最老一条已经等了 30 分钟
```

因为不同业务正常 backlog 数量不同。

---

# 14. Agent / LLM 服务还需要哪些信号

除了普通后端：

```text
request success / error
latency
```

还可能关注：

```text
model/provider
first-token latency
full completion latency
input tokens
output tokens
cost
number of tool calls
tool error rate
retrieval latency
retrieval result count
no-source rate
cancel rate
budget exceeded
```

但不要给 metric label 放：

```text
user prompt
request_id
full document id（超高基数时）
```

---

# 15. Cardinality 是什么

Metric label：

```text
route=/tickets
status=200
```

取值有限，通常合理。

如果 label：

```text
request_id=req_12345...
```

每个请求都不同。

时间序列数量会爆炸。

这叫 high cardinality。

所以：

```text
request_id 更适合 log/trace
```

而不是 metric label。

---

# 16. Liveness 和 Readiness 一定要分清

## Liveness

问：

> 这个进程是否已经坏到应该重启？

例如：

```text
主事件循环彻底死锁
```

可能 liveness fail。

## Readiness

问：

> 这个实例现在是否应该继续接新流量？

例如数据库不可用：

```text
API 进程仍活着
但无法完成核心请求
```

可能：

```text
liveness = OK
readiness = FAIL
```

这样负载均衡器停止发新请求，但容器不必不断重启。

---

# 17. 为什么 healthz 不应该什么都检查

如果 liveness 每次都查询数据库：

```text
DB 短暂故障
↓
所有实例 liveness fail
↓
K8s 全部重启
↓
启动又要访问 DB
↓
故障风暴
```

所以本仓库 `/healthz` 故意不访问数据库。

数据库健康更适合影响 readiness，而不是简单等同 liveness。

---

# 18. Startup Probe 是什么

某些应用启动很慢：

```text
加载模型
预热索引
初始化大数据
```

如果普通 liveness 很早开始检查：

```text
应用还没启动完
→ 被认为死了
→ 重启
→ 永远启动不完
```

Startup probe 可以给初始化一个独立窗口。

不是所有普通 Go API 都需要它。

---

# 19. SLI、SLO、SLA 分清

## SLI

Service Level Indicator：测量值。

例如：

```text
成功请求比例
P95 latency
```

## SLO

Service Level Objective：内部目标。

例如：

```text
30 天内 99.9% create-ticket 请求成功
```

## SLA

Service Level Agreement：对外合同/承诺，可能伴随赔付。

不要把三者当同一个词。

---

# 20. 为什么 SLO 要用户导向

差：

```text
CPU < 70%
```

这可能是一个资源目标，但用户并不直接关心 CPU。

更用户导向：

```text
创建工单成功率 >= 99.9%
P95 < 300ms
```

CPU 可以作为诊断信号。

SLO 应尽量表达用户是否得到服务。

---

# 21. Error Budget 是什么

SLO：

```text
99.9% success
```

意味着允许：

```text
0.1% failure budget
```

这个允许的失败量就是 error budget 的基本概念。

如果预算快速耗尽：

```text
减少高风险发布
优先修可靠性
```

它让“速度 vs 稳定性”不再只靠争论。

---

# 22. Alert 不是“任何异常都通知人”

差的告警：

```text
CPU > 50% 立即 Pager
```

结果：

```text
每天几十条
没有实际用户影响
人开始忽略
```

好的告警要问：

```text
它代表真实用户影响或即将容量耗尽吗？
值班人收到以后有明确行动吗？
持续多久才值得叫醒人？
```

例如：

```text
create-ticket 5xx > 5%
持续 10 分钟
且 QPS > 某最小值
```

阈值仍需基于真实基线校准。

---

# 23. Dashboard 和 Alert 的职责不同

Dashboard：

```text
帮助观察和诊断
```

Alert：

```text
主动告诉人必须关注
```

不是 Dashboard 上每一个图都需要一条 Alert。

---

# 24. Logging Level 怎么理解

常见：

```text
DEBUG
INFO
WARN
ERROR
```

不要只按“严重程度感觉”写。

例如：

```text
用户传非法参数
```

是正常业务输入错误，未必需要 ERROR。

真正 ERROR 更适合：

```text
服务无法完成一个本应成功的操作
```

同一个已处理错误不要在每层重复 ERROR 五次，否则一个故障变成大量重复报警日志。

---

# 25. Error Code 比文案更适合聚合

日志：

```text
message="database call took too long"
```

以后文案可能修改。

稳定字段：

```text
error_code="db_timeout"
```

可以稳定统计。

这和 API response 中使用机器 error code 是同一思维。

---

# 26. Observability 也有开销

Trace 100% 采样、大量 DEBUG logs、高基数 metrics：

```text
都要花钱和资源
```

需要：

- log retention；
- sampling；
- metric cardinality budget；
- PII policy；
- telemetry pipeline capacity。

所以可观测性不是“加得越多越专业”。

---

# 27. 本仓库怎么练

运行：

```powershell
python exercises/reliability-labs/metrics_demo.py
```

访问：

```text
/healthz
/readyz
/metrics
```

观察三种 endpoint 的职责区别。

然后为一个 Ticket API 设计：

### HTTP metrics

```text
request rate
error rate
latency histogram
```

### DB metrics

```text
pool in-use
pool wait
query timeout
```

### Async metrics

```text
outbox pending
oldest unpublished age
stream pending age
retry / DLQ
```

### Agent metrics

```text
provider latency
tool error
input/output tokens
cost
budget exceeded
```

每个 metric 都回答：

> 它异常以后我准备做什么？

---

# 28. 一个完整排障例子

用户反馈：

```text
创建工单很慢
```

先看 Metric：

```text
P95 从 200ms -> 3s
error rate 正常
```

Trace：

```text
API 50ms
DB pool wait 2600ms
query 100ms
```

Resource metric：

```text
DB pool saturated
```

Logs：

```text
pool_acquire_timeout increasing
```

现在根因假设可以聚焦：

```text
不是 Handler CPU 慢
而是连接池等待
```

这就是三个 signal 配合的价值。

---

# 29. 常见误区

## 日志越多越好

错误。关键是结构、关联和安全。

## 有 Request ID 就等于有 Trace

错误。Trace 还表达跨 span 的父子关系和耗时。

## Average latency 足够

错误。尾延迟经常影响用户。

## CPU 高就是故障

不一定。要关联用户 SLI 和资源饱和情况。

## 健康检查越深越好

错误。Liveness 检查过多外部依赖可能制造重启风暴。

## 只要 200 就健康

错误。异步 backlog、延迟和业务质量都可能已经恶化。

## 所有错误都应该 ERROR log

错误。很多 4xx 是预期业务结果。

---

# 30. 关闭文档复述

1. Log、Metric、Trace 各自主要回答什么？
2. 为什么结构化日志不是简单把字符串改成 JSON 就结束？
3. Request ID 和 Trace ID 有什么区别？
4. 为什么 Token/Prompt 等内容不能为了调试随便进日志？
5. Average 和 P95/P99 的信息差在哪？
6. RED 分别是什么？
7. 为什么异步系统要看 oldest backlog age？
8. Metric high cardinality 为什么危险？
9. Liveness 和 Readiness 的区别是什么？
10. 为什么数据库挂掉通常不应该直接让 liveness 失败？
11. SLI / SLO / SLA 分别是什么？
12. Error Budget 怎么帮助团队做取舍？
13. 好 Alert 为什么必须具有行动性？
14. Agent 服务除了普通 RED，还需要观察哪些预算/工具信号？
15. Observability 自己为什么也需要成本和隐私边界？

如果用户只说一句“刚才很慢”，你能想到先看哪些信号、怎样逐层缩小范围，本课就开始真正有用了。
