# 第 12 课：日志、指标、Trace 和 SLO

## 三类信号

- Log：一次具体事件的上下文；
- Metric：随时间聚合的数值趋势；
- Trace：一次请求跨服务的调用路径和耗时。

它们互补，不能用海量日志替代指标，也不能只看平均耗时。

## 结构化日志

最小字段：

```text
timestamp, level, service, env, version,
request_id, trace_id, event_id,
operation, outcome, duration_ms, error_code
```

不要把 Token、密码、密钥、完整隐私数据或未经控制的模型输入写入日志。

## RED 和异步指标

HTTP 服务关注：

- Rate：请求量；
- Errors：错误率；
- Duration：P50/P95/P99。

异步系统还关注：

- Stream backlog；
- Pending 数量和最老消息年龄；
- retry/DLQ；
- 任务等待、执行、租约过期；
- Outbox 未发布数量。

AI 服务还应记录成功率、首 Token 延迟、总耗时、输入输出 Token、工具错误和成本，但控制标签基数。

## Probe

- liveness：进程是否需要重启；
- readiness：是否应该接收流量；
- startup：慢启动服务是否已经完成初始化。

数据库不可用时，readiness 通常失败；liveness 不应因此不断重启并形成风暴。

## SLO

SLO 是用户可感知目标，例如“工单创建 99.9% 成功、P95 小于 300ms”。告警应该指向用户影响或即将发生的容量问题。

## 练习

为创建工单、Webhook、Outbox Publisher、Stream Consumer 和 Agent Task 各设计两个指标，并说明告警阈值需要通过什么数据校准。
