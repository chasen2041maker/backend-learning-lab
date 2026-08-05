# PostgreSQL 练习

第 5 周开始使用。先在 `exercises/infrastructure` 启动数据库：

```powershell
docker compose up -d postgres
docker compose exec postgres psql -U lab -d backend_lab
```

在 `psql` 中：

```sql
\i /workspace/schema.sql
\i /workspace/seed.sql
```

如果没有挂载本目录，可以复制 SQL 内容执行，或从宿主机使用 PostgreSQL 客户端。

## 学习任务

1. 查看每个约束解决什么问题；
2. 为 `tenant_demo` 查询最新 20 个工单；
3. 完成游标分页；
4. 使用 `EXPLAIN (ANALYZE, BUFFERS)` 查看索引；
5. 在事务中记录 Webhook、更新工单并写 Outbox；
6. 重复插入相同 provider/event_id，观察唯一冲突；
7. 使用 `version` 实现乐观更新。

## Outbox 恢复协议

阅读并逐句解释 `outbox-protocol.sql`。其中 `:name` 是数据库驱动占位符参考，不能直接用 `psql \i` 执行。Publisher 使用短事务领取批次，网络发布期间不持有行锁；完成/失败更新必须匹配 `worker_id + lease_token`，否则旧 Worker 被 fencing 拒绝。连续失败采用有上限的指数退避，第 8 次进入 DLQ 状态。

可执行的 PostgreSQL 验证位于 `tests/outbox-integration.sql`，覆盖 claim、lease expiry、reclaim、fencing、retry 和第 8 次进入 DLQ。

关键失败窗口是“消息已发布，但 `published_at` 尚未提交”。因此这里只能保证至少一次，消费者仍必须按 `event_id` 幂等。
