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
