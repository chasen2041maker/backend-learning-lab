# PostgreSQL 实验：让数据库真正承担“事实正确性”

这个目录不是 SQL 语法题库。它用于证明一个后端核心变化：

```text
内存状态
→ PostgreSQL 事实源
```

一旦业务事实进入数据库，你必须开始考虑的不只是“能 INSERT/SELECT”，还包括：

```text
schema constraint
query/index
transaction
concurrent update
idempotency
outbox/recovery
```

先阅读 [`lessons/05-sql-postgresql.md`](../../lessons/05-sql-postgresql.md) 和 [`lessons/06-transactions-idempotency.md`](../../lessons/06-transactions-idempotency.md)。

## 1. 启动本地 PostgreSQL

```powershell
cd exercises\infrastructure
docker compose up -d postgres
docker compose exec postgres pg_isready -U lab -d backend_lab
```

然后进入数据库：

```powershell
docker compose exec postgres psql -U lab -d backend_lab
```

如果 SQL 文件没有挂载到容器，可以从宿主机客户端执行，或复制相应 SQL。不要因为路径问题就把 schema 逻辑改掉。

## 2. 先认识每个文件负责什么

```text
schema.sql
→ 表、PK/FK/UNIQUE/CHECK、索引等事实边界

seed.sql
→ 纯学习数据

challenges.sql
→ 留给你完成的查询/修改

reference-queries.sql
→ 部分参考，不是第一步

outbox-protocol.sql
→ Outbox claim/lease/fencing/retry 协议说明

tests/outbox-integration.sql
→ 真 PostgreSQL 上验证 claim/reclaim/fencing/DLQ
```

## 3. 第一组实验：Constraint 不是“多余校验”

先查看 `schema.sql`，逐个回答：

```text
如果删掉这个 NOT NULL / UNIQUE / CHECK / FK，
什么非法事实就可能进入数据库？
```

然后故意插入：

- 非法状态；
- 重复唯一值；
- 不存在的引用；
- 违反 tenant/business invariant 的数据（如果 schema 有对应约束）。

观察 PostgreSQL 返回的错误。

心智模型：

> 应用验证改善错误体验；数据库约束守住最终事实。二者不是二选一。

## 4. 第二组实验：Index 从查询形状推导

不要先问“应该建什么索引”。先写真实查询：

```text
某 tenant
按 created_at DESC, id DESC
取最新 20 条
```

再运行：

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

记录：

```text
filter：
order：
limit：
使用的 index：
rows estimated / actual：
buffers：
```

然后临时比较有/无合适索引的执行计划。

不要只留下：

```text
“建索引之后更快”
```

你应该能解释**这个索引为什么匹配这个查询**。

## 5. Cursor Pagination

先定义稳定排序：

```text
(created_at DESC, id DESC)
```

然后第二页条件必须表达：

```text
“严格位于上一页最后一条之后”
```

测试：

- 相同 `created_at` 多条记录；
- 新数据在翻页期间插入；
- cursor 边界为空；
- tenant 条件不能因为分页而丢失。

## 6. Optimistic Version：证明 lost update 被检测

制造：

```text
A read version=1
B read version=1
A update WHERE version=1 -> success, version=2
B update WHERE version=1 -> 0 rows
```

重点不是 SQL 写法，而是：

```text
0 rows
```

如何被 Service 分类成 conflict，而不是“数据库好像没改到”。

## 7. Transaction：先画边界再写 BEGIN/COMMIT

对于“处理 Webhook + 更新 Ticket + 写 Outbox”，画：

```text
BEGIN
  dedupe provider event
  update business fact
  insert outbox row
COMMIT
```

然后分别问：

```text
COMMIT 前崩溃？
COMMIT 后 HTTP response 前崩溃？
外部 publish 能不能被 DB rollback？
```

这三个问题解释了 transaction、idempotency 和 Outbox 为什么是不同概念。

## 8. Outbox 恢复协议

`outbox-protocol.sql` 是协议参考，不是可以直接 `psql \i` 执行的完整脚本；其中 `:name` 表示数据库驱动参数占位概念。

重点流程：

```text
claim short transaction
→ commit claim
→ 网络 publish（不持有 DB row lock）
→ mark success/failure
```

完成/失败写回必须匹配：

```text
worker_id + lease_token
```

否则旧 Worker 在 lease 过期并被别人接管后仍可能写回，这就是 fencing 要防的问题。

运行集成验证时重点观察：

- claim；
- lease expiry；
- reclaim；
- stale worker fencing；
- bounded retry；
- 第 8 次失败进入 DLQ 状态。

## 9. Outbox 仍然会重复

关键失败窗口：

```text
消息 publish 成功
↓
进程崩溃
↓
数据库还没提交 published_at
```

恢复后 Publisher 会再次发布。

因此 Outbox 解决的是：

```text
业务事实和“需要发布”不会因双写窗口永久分叉
```

它**不保证 exactly-once delivery**。Consumer 仍需要按 `event_id` 幂等。

## 10. 实验完成证据

不要只写 SQL 文件已执行。至少记录：

```text
一个 constraint 失败：
一个 EXPLAIN 对比：
一个 optimistic conflict：
一个 COMMIT 后 response 前失败分析：
一个 Outbox 重复发布窗口：
一个 stale worker fencing 结果：
```

关闭文档后应该能回答：

1. 为什么应用校验不能替代数据库 constraint？
2. 为什么 index 必须从 query shape 推导？
3. transaction 能不能撤销已经发送的 HTTP/邮件？
4. optimistic lock 和 pessimistic lock 各在防什么？
5. Outbox 保证什么、不保证什么？
6. 为什么 Publisher 不应该网络 publish 时一直持有数据库行锁？
