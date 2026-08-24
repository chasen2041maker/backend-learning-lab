# Python FastAPI 工单练习：观察完整 API，而不是把框架当答案

这个目录是课程前半段的**可运行 Python HTTP 基线**。它故意使用内存 Repository，让你先把 HTTP、输入验证、分层、可信身份、状态机、错误响应和测试讲清楚，再把持久化复杂度加进来。

不要把它理解成：

> FastAPI 项目应该永远长这样。

真正要学的是框架下面的稳定边界。

## 运行

```powershell
python -m pip install -r ..\..\requirements-repo.lock
python -m pip install --no-deps -e .
python -m pytest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Swagger UI：

```text
http://127.0.0.1:8000/docs
```

除 `/health` 外，示例使用教学凭据：

```http
Authorization: Bearer lab-token-tenant-a
```

它不是生产认证方案。这里要证明的是：只有服务端验证后的 credential 才能产生可信 `Principal`，客户端不能通过 Body/Query 自报 `tenant_id`。

## 先画请求链再看代码

```text
HTTP Request
   ↓
FastAPI routing/dependency
   ↓
input model / Principal
   ↓
Handler
   ↓
Service
   ↓
Repository
   ↓
in-memory facts
   ↓
response/error mapping
```

推荐阅读顺序：

1. tests：先看系统承诺什么；
2. `app/main.py`：HTTP、dependency、error mapping；
3. `models.py`：输入/输出和领域数据；
4. `service.py`：业务规则；
5. `repository.py`：事实存取与 tenant 范围；
6. `errors.py`：内部错误语义。

## 已实现的能力

- create/get/list/close Ticket；
- strict input 和稳定 machine code；
- request ID；
- tenant-scoped Principal；
- 乐观 version close；
- Python/Go 共享契约测试；
- Handler/Service/Repository 分层。

## 当前实现故意没有证明什么

内存 Repository 意味着：

```text
process restart
→ facts disappear
```

当前测试也不证明：

- PostgreSQL constraint/transaction；
- connection pool/statement timeout；
- JWT/Refresh Token；
- 多实例一致性；
- Redis/queue；
- 生产容量和安全配置。

这些不是“缺陷没补完”，而是学习顺序上的刻意边界。

## 独立扩展不要同时做五个

一次选一个：

### `priority`

先定义契约、非法值和默认值，再写失败测试。

### `reopen`

先写状态机：只允许 `closed -> open`，再决定 API 形状。不要先加路由再想规则。

### cursor pagination

先明确稳定排序 `(created_at, id)`，再设计 cursor 编解码和边界测试。

### PostgreSQL Repository

保持 Handler/Service 语义尽量不变，只替换事实存储；加入 migration、constraint、transaction 和 integration test。

## 做完一个修改后必须回答

```text
我改的是协议、业务还是存储？
为什么放在这一层？
哪个测试先失败？
哪个测试证明修复？
如果进程/DB/网络在这里失败会怎样？
当前 fake/内存实现没有证明什么？
```

如果只是看 `/docs` 能调用成功，还不能算掌握。真正的目标是：换掉 FastAPI 以后，你仍然知道这套后端为什么这样分层。
