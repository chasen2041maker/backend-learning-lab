# 第 5 课：PostgreSQL 保存业务事实

## 表不是 Excel

数据库除了存值，还要通过约束保护事实：

```sql
CREATE TABLE tickets (
    id uuid PRIMARY KEY,
    tenant_id text NOT NULL,
    title text NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    status text NOT NULL CHECK (status IN ('open', 'closed')),
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

即使 API 已经验证，数据库约束仍然重要，因为后台任务、迁移或其他服务也可能写入。

## 索引从查询出发

```sql
CREATE INDEX idx_tickets_tenant_created
ON tickets (tenant_id, created_at DESC, id DESC);
```

它适合：

```sql
WHERE tenant_id = $1
ORDER BY created_at DESC, id DESC
```

不是“字段重要就建索引”。索引增加写入、空间和维护成本。

## 参数化查询

永远不要拼接用户输入：

```sql
SELECT * FROM tickets WHERE tenant_id = $1 AND id = $2;
```

参数化不仅防 SQL 注入，也有利于计划复用。

## N+1

先查 100 个工单，再对每个工单单独查询用户，会产生 101 次查询。解决方式可能是 JOIN、批量 `IN`、预加载或重新设计读模型。

## 事务之外的思考

- 哪个服务拥有这张表？
- 其他服务如何读取或请求修改？
- 如何备份和恢复？
- 数据保留多久？
- 查询是否始终带 `tenant_id`？

## 练习

运行 `exercises/sql-postgres`：创建表、插入数据、比较索引、完成游标分页，并解释每个查询为什么能或不能使用索引。
