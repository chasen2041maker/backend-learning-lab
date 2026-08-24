# 第 5 课：SQL 与 PostgreSQL——后端的“事实层”到底是什么

很多初学者第一次接数据库，会把它理解成“一个可以存东西的表格”。

这不够。

后端真正需要数据库解决的是：

> **多个请求、多个进程、程序重启甚至机器故障之后，哪些业务事实仍然必须存在，而且不能随便变成非法状态？**

这就是本课的核心。

---

## 1. 先理解数据库在请求链中的位置

没有数据库时：

```text
HTTP Request
    ↓
Handler
    ↓
Service
    ↓
Memory Repository
    ↓
map / dict
```

程序退出：

```text
内存消失
→ 工单全部没了
```

接 PostgreSQL 后：

```text
HTTP Request
    ↓
Handler
    ↓
Service
    ↓
Repository
    ↓
PostgreSQL
```

数据库是独立进程。

应用程序退出，不等于 PostgreSQL 数据消失。

所以先记：

> Repository 是“业务代码如何访问事实”的边界；PostgreSQL 是事实真正持久化的位置之一。

---

# 2. PostgreSQL 不只是一个文件

PostgreSQL 是一个数据库服务器进程。

应用通常通过网络连接：

```text
Go / Python App
      |
      | TCP connection
      v
PostgreSQL Server
      |
      v
Database
      |
      v
Table
```

所以数据库也会出现网络型问题：

```text
connection refused
连接超时
连接池耗尽
statement timeout
数据库重启
```

不要把所有 SQL 错误都理解成“SQL 写错了”。

---

# 3. Table / Row / Column 到底是什么

例如：

```sql
CREATE TABLE tickets (
    id uuid PRIMARY KEY,
    tenant_id text NOT NULL,
    title text NOT NULL,
    status text NOT NULL,
    version bigint NOT NULL,
    created_at timestamptz NOT NULL
);
```

可以粗略理解：

```text
tickets 表

id          tenant_id   title      status   version
---------------------------------------------------
abc...      tenant_a    无法登录    open     1
xyz...      tenant_a    支付失败    closed   3
```

但数据库表比 Excel 多了一个非常重要的能力：

> **数据库可以定义“什么数据根本不允许存在”。**

---

# 4. Constraint：不要只靠应用代码保护数据

假设 Service 已经检查：

```text
status 只能是 open / closed
```

是不是数据库就不用检查了？

不是。

因为以后可能还有：

```text
后台任务
migration
管理脚本
另一个服务
人工 SQL
```

直接写数据库。

所以数据库也应该保护不变量。

例如：

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

这里的约束：

### `NOT NULL`

不允许没有值：

```sql
tenant_id text NOT NULL
```

### `CHECK`

限制合法范围：

```sql
CHECK (status IN ('open', 'closed'))
```

### `PRIMARY KEY`

每一行的唯一身份：

```sql
id uuid PRIMARY KEY
```

### `UNIQUE`

例如邮件不能重复：

```sql
email text UNIQUE
```

### `FOREIGN KEY`

表达两张表之间的引用关系：

```sql
CREATE TABLE comments (
    id uuid PRIMARY KEY,
    ticket_id uuid NOT NULL REFERENCES tickets(id)
);
```

意思不是“数据库自动帮你 JOIN”。

它表达的是：

> 这个 comment 不能随便指向一个根本不存在的 ticket。

---

# 5. CRUD 只是 SQL 的入口

最基础四种操作：

```text
Create  -> INSERT
Read    -> SELECT
Update  -> UPDATE
Delete  -> DELETE
```

例如：

```sql
INSERT INTO tickets (id, tenant_id, title, status)
VALUES ($1, $2, $3, 'open');
```

查询：

```sql
SELECT id, title, status
FROM tickets
WHERE tenant_id = $1;
```

更新：

```sql
UPDATE tickets
SET status = 'closed'
WHERE id = $1 AND tenant_id = $2;
```

删除：

```sql
DELETE FROM tickets
WHERE id = $1 AND tenant_id = $2;
```

注意每一个业务查询都出现：

```text
tenant_id
```

这是数据隔离的一部分，不是“前端已经筛选过所以数据库不用管”。

---

# 6. 参数化查询：不要拼接用户输入

错误：

```text
"SELECT * FROM users WHERE name = '" + userInput + "'"
```

如果输入包含 SQL 片段，就可能产生 SQL Injection。

正确方向：

```sql
SELECT *
FROM users
WHERE name = $1;
```

然后把值作为参数传给驱动。

概念上：

```text
SQL structure
和
user data
分开传输
```

不是靠：

```text
我自己 replace 单引号
```

来防注入。

---

# 7. JOIN：数据分表以后怎么组合

假设：

```text
users
id | name

 tickets
id | owner_id | title
```

要查询工单和用户名：

```sql
SELECT
    t.id,
    t.title,
    u.name
FROM tickets AS t
JOIN users AS u
  ON u.id = t.owner_id
WHERE t.tenant_id = $1;
```

心智模型：

```text
tickets 的每一行
根据 owner_id
去匹配 users.id
```

JOIN 不是“高级 SQL”，而是关系型数据库最核心的能力之一。

---

# 8. GROUP BY：从行变成统计

例如统计每个状态多少工单：

```sql
SELECT status, COUNT(*)
FROM tickets
WHERE tenant_id = $1
GROUP BY status;
```

结果可能是：

```text
open    23
closed  97
```

区别：

```text
WHERE
先过滤行

GROUP BY
再按某些字段分组

COUNT / SUM / AVG
对组做聚合
```

---

# 9. Index 到底解决什么

假设表里有 1000 万行。

查询：

```sql
SELECT *
FROM tickets
WHERE tenant_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

没有合适索引时，数据库可能需要扫描大量行。

索引可以让数据库更快定位数据。

例如：

```sql
CREATE INDEX idx_tickets_tenant_created
ON tickets (tenant_id, created_at DESC, id DESC);
```

这个索引是从**真实查询形状**推导出来的：

```text
WHERE tenant_id = ?
ORDER BY created_at DESC, id DESC
```

不是因为：

> `created_at` 很重要，所以我要给它加索引。

---

# 10. 索引不是免费的

每增加索引，数据库写入时通常也要维护它。

所以会增加：

```text
INSERT 成本
UPDATE 成本
DELETE 成本
磁盘空间
VACUUM / maintenance 成本
```

因此：

> 索引应该由查询模式驱动，而不是“每个 WHERE 字段都建一个”。

---

# 11. 组合索引为什么字段顺序重要

例如：

```sql
CREATE INDEX idx_demo
ON tickets (tenant_id, status, created_at);
```

它和：

```sql
(status, tenant_id, created_at)
```

不是同一个索引。

索引的列顺序需要结合：

- equality 条件；
- range 条件；
- sort；
- 选择性；
- 实际 PostgreSQL query plan。

基础阶段不要死背“最左匹配”当万能规则；真正判断用：

```sql
EXPLAIN
```

或：

```sql
EXPLAIN ANALYZE
```

看 PostgreSQL 实际执行计划。

---

# 12. EXPLAIN：不要猜数据库在干什么

例如：

```sql
EXPLAIN
SELECT id, title
FROM tickets
WHERE tenant_id = 'tenant_a';
```

可能看到：

```text
Seq Scan
```

或者：

```text
Index Scan
Bitmap Index Scan
```

不要形成新误区：

> Seq Scan 一定是错的。

如果表很小、查询本来要读取大部分行，Sequential Scan 可能就是更便宜的方案。

所以重点是：

```text
数据库为什么选择这个 plan？
这个 plan 在当前数据规模是否合理？
```

---

# 13. Cursor Pagination 为什么比超大 OFFSET 更适合很多 API

常见分页：

```sql
OFFSET 100000
LIMIT 20
```

数据库仍可能需要走过大量前面的结果。

而且在新数据不断插入时，offset 页可能发生漂移。

一种游标分页：

```sql
SELECT id, title, created_at
FROM tickets
WHERE tenant_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

这里：

```text
(created_at, id)
```

共同构成稳定位置。

为什么还要 `id`？

因为多个记录可能有相同 `created_at`，只用时间可能无法稳定排序。

---

# 14. N+1 是什么

假设先查：

```text
100 tickets
```

然后循环：

```text
ticket 1 -> query user
 ticket 2 -> query user
...
ticket 100 -> query user
```

总共：

```text
1 + 100 = 101 queries
```

这就是典型 N+1。

可能的处理：

- JOIN；
- 批量查询；
- 数据加载器；
- 合理的读模型。

不要机械地认为“JOIN 总是最好”，但要能看出隐藏的大量数据库 round trip。

---

# 15. Connection Pool 为什么存在

应用不是每个请求都应该：

```text
新建 TCP connection
认证数据库
执行一条 SQL
立即断开
```

建立连接本身有成本。

所以一般会使用连接池：

```text
App
  |
  v
Connection Pool
 | | | |
 v v v v
PostgreSQL connections
```

但连接池不是“越大越快”。

假设：

```text
10 个应用实例
每个 pool = 100
```

理论上可能打到：

```text
1000 database connections
```

这可能反而把数据库压垮。

所以连接池属于资源预算问题。

---

# 16. Timeout 也必须有

数据库调用可能：

```text
等锁
慢查询
网络卡住
连接池排队
```

后端不能无限等。

需要区分：

```text
获取连接 timeout
statement timeout
整个 request deadline
```

它们不是同一个东西。

下一课事务里会继续讨论锁和超时。

---

# 17. Migration 是什么

你的代码会升级：

```text
v1: tickets 没有 priority
v2: tickets 增加 priority
```

数据库 schema 也必须演进。

Migration 就是可追踪的 schema 变化：

```text
001_create_tickets.sql
002_add_priority.sql
003_add_ticket_index.sql
```

不要把生产数据库 schema 依赖于：

```text
应用启动时自动“发现不一样就乱改表”
```

大型迁移还会涉及：

- table lock；
- rewrite；
- 长事务；
- 新旧版本兼容；
- rollback 是否真实可行。

---

# 18. PostgreSQL 是事实源，不代表所有东西都必须放 PostgreSQL

典型：

```text
订单最终状态 -> PostgreSQL
缓存 -> Redis
文件 -> Object Storage
搜索投影 -> Search Engine
实时连接 -> memory/Redis
```

关键不是“哪个数据库最好”，而是：

> 谁是 authoritative source of truth？其他数据丢掉后能不能重建？

---

# 19. 多租户查询必须守住数据边界

危险代码：

```sql
SELECT *
FROM tickets
WHERE id = $1;
```

如果这是多租户系统，知道另一个租户的 ID 可能直接读到数据。

更合理：

```sql
SELECT *
FROM tickets
WHERE id = $1
  AND tenant_id = $2;
```

这里 `$2` 应来自服务端可信 Principal，而不是客户端 Body 自报。

安全边界必须一路落到数据访问层。

---

# 20. 常见误区

## 误区 1：API 已校验，数据库约束就没必要

错。

应用不是数据库的唯一写入路径，而且 bug 总会存在。

## 误区 2：索引越多查询越快

错。

索引有写入和维护成本，而且未必被 query planner 使用。

## 误区 3：看到 Seq Scan 就一定要加索引

错。

小表或读取大部分数据时 Seq Scan 可能最优。

## 误区 4：Repository 就是“把 SQL 单独放一个文件”

不完整。

Repository 的意义是隔离数据访问语义和业务层，让 Service 不依赖具体存储细节。

## 误区 5：Redis 更快，所以事实也放 Redis

这是下一课之后仍要反复警惕的错误。速度不是唯一约束。

---

# 21. 本仓库实验

进入：

```powershell
cd exercises\sql-postgres
```

重点不要只看参考 SQL。

建议依次验证：

1. schema 能从空库创建；
2. 非法 status 被 constraint 拒绝；
3. 重复唯一键被拒绝；
4. tenant A 查询不到 tenant B 数据；
5. 一个真实列表查询加索引前后的 `EXPLAIN`；
6. 游标分页的下一页没有重复；
7. 手工尝试一个 N+1，再改成批量/JOIN。

记录的证据应该包含：

```text
SQL
预期
实际输出
query plan
我为什么这样设计
```

---

# 22. 关闭文档以后回答

1. PostgreSQL 和你的 Go/Python 进程是什么关系？
2. 为什么表不是“Excel 放到服务器上”？
3. PRIMARY KEY、UNIQUE、FOREIGN KEY 分别在保护什么？
4. 为什么 API 已验证仍然需要数据库约束？
5. 参数化查询为什么能降低 SQL Injection 风险？
6. 什么是 N+1？
7. 索引为什么不能“重要字段全加”？
8. 为什么 `EXPLAIN` 比猜测更可靠？
9. Connection Pool 为什么不是越大越好？
10. 为什么多租户过滤必须进入 Repository/SQL？
11. 为什么业务事实和缓存不是同一个概念？
12. Migration 为什么是后端工程的一部分？

如果这些问题都能讲清楚，再进入事务、锁和幂等会自然很多。
