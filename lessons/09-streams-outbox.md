# 第 9 课：Outbox、Redis Streams 与可恢复任务

## 双写问题

下面的代码无法原子完成：

```text
1. 更新 PostgreSQL 工单
2. 向 Redis 发布 ticket.closed
```

如果第 1 步成功、第 2 步失败，状态已经改变但消费者永远不知道。反过来先发消息也会产生“消息存在、数据库回滚”。

## Transactional Outbox

在同一个 PostgreSQL 事务中：

```text
更新 tickets
插入 outbox_events
提交
```

独立 publisher 轮询未发布 Outbox，发送到 Redis Streams，成功后记录发布时间。Publisher 可以重复发送，因此消费者仍必须幂等。

## Redis Streams 核心概念

- Stream：按 ID 排序的消息日志；
- Consumer Group：一组消费者协作处理；
- Pending：已投递但尚未 ACK；
- ACK：消费者确认完成；
- Claim：接管超时 Pending；
- DLQ：多次失败后的隔离区，不是垃圾桶。

## ACK 时机

业务处理成功并持久化以后再 ACK。

```text
读取消息
→ 检查 event_id 是否已处理
→ 应用业务事务
→ 记录处理结果
→ ACK
```

如果业务提交后、ACK 前宕机，消息会再次投递。幂等记录让第二次处理安全返回。

## 租约和围栏

长任务需要 lease 允许故障接管。但旧 Worker 可能在租约过期后恢复并写入旧结果。Fencing token/版本号让数据库拒绝旧 Worker 的写入。

## 练习

完成 Redis Lab 后，手工制造消费者在 ACK 前退出，再启动消费者，观察 Pending 被重新处理且业务结果没有重复。
