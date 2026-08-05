# 第 1 课：第一次运行后端服务

预计用时：75～90 分钟。实验数量：4 个主实验、8 个故障实验、1 组失败测试。

## 你将亲手完成什么

完成本课后，你能够：

- 启动一个 Python 后端进程，并指出监听地址与端口；
- 用 `curl.exe -v` 区分请求行、Header、Body、状态行和响应 Body；
- 解释连接失败为什么不是 HTTP `404` 或 `500`；
- 使用教学 Token 创建工单，并核对响应 Header 与 Body 中的 request ID；
- 根据证据区分 `400`、`401`、`404`、`422` 和 `500`；
- 画出当前代码真实存在的请求链路，不提前加入 PostgreSQL、BFF 或 Outbox。

## 前置条件

在仓库根目录执行：

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -c "import fastapi, pydantic, uvicorn; print('python dependencies ready')"
```

关键输出应包含：

```text
Python 3.11 或更高版本
python dependencies ready
```

如果最后一条失败，按[环境准备](00b-environment-setup.md)使用当前 Python 安装根目录锁文件。

## 本课不讲什么

本课不需要 Docker、PostgreSQL、Redis、Go，也不会讲事务或幂等。

## 当前项目状态

本课直接运行现有服务 [python-ticket-api](../exercises/python-ticket-api/README.md)。当前数据只保存在
`InMemoryTicketRepository` 的进程内存中。停止进程后，刚创建的工单会消失。

服务已有以下接口：

| 请求 | 作用 | 是否需要 Token |
| --- | --- | --- |
| `GET /health` | 判断 HTTP 进程能否响应 | 否 |
| `POST /api/v1/tickets` | 创建工单 | 是 |
| `GET /api/v1/tickets/{id}` | 查询工单 | 是 |

## 实验 1：从源代码到监听端口

打开第一个 PowerShell 窗口：

```powershell
cd exercises\python-ticket-api
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

关键输出类似：

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process [...]
INFO:     Started server process [...]
INFO:     Application startup complete.
```

输出中的数字会变化，不需要逐字相同。

- `app.main:app` 表示导入 `app/main.py` 中名为 `app` 的对象；
- `python -m uvicorn` 启动 Python 进程，源文件本身不会监听网络；
- `127.0.0.1` 是本机回环地址，其他电脑不能通过它访问这个服务；
- `8000` 是端口，操作系统把到达该地址和端口的连接交给此进程；
- `--reload` 启动监视进程，源文件变化后重启服务，仅用于本地开发。

保持第一个窗口运行，打开第二个 PowerShell 窗口：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  Select-Object LocalAddress, LocalPort, State, OwningProcess
```

关键输出：

```text
LocalAddress LocalPort State  OwningProcess
------------ --------- -----  -------------
127.0.0.1         8000 Listen ...
```

如果系统不允许读取 TCP 连接，使用：

```powershell
netstat -ano | Select-String "127.0.0.1:8000"
```

你刚证明了三件不同的事：文件存在、Python 进程正在运行、该进程正在监听端口。

## 实验 2：观察第一个 HTTP 请求

在第二个窗口运行：

```powershell
curl.exe -v http://127.0.0.1:8000/health
```

`curl` 版本不同会显示额外信息，只寻找这些关键行：

```text
> GET /health HTTP/1.1
> Host: 127.0.0.1:8000
< HTTP/1.1 200 OK
< content-type: application/json
{"status":"ok"}
```

`>` 表示客户端发出的内容，`<` 表示服务端返回的内容。

```text
GET            Method，请求想读取资源
/health        Path，服务内的路由位置
HTTP/1.1       本次使用的协议版本
Host           目标主机与端口
200 OK         状态行，HTTP 请求已被服务处理
content-type   Header，说明 Body 是 JSON
{"status":"ok"}  响应 Body
```

这次请求没有业务 JSON Body。`GET` 请求不是“永远不能有 Body”，而是本接口的契约不需要。

## 故障实验 1：停止服务

回到第一个窗口按 `Ctrl+C`，等进程退出，再运行：

```powershell
curl.exe -v http://127.0.0.1:8000/health
```

Windows curl 的文字和失败速度可能因本机网络栈不同而变化，常见结果是：

```text
Failed to connect to 127.0.0.1 port 8000
```

也可能等待几秒后显示 `Connection timed out`。两者的关键含义相同：8000 端口没有给客户端返回 HTTP 响应。

此时没有状态码，因为客户端根本没有收到 HTTP 响应。对比：

| 现象 | 连接建立了吗 | 收到 HTTP 响应了吗 |
| --- | --- | --- |
| 连接被拒绝或超时 | 否 | 否 |
| `404` | 是 | 是，路由或资源不存在 |
| `500` | 是 | 是，服务处理时发生未预期错误 |
| `503` | 是 | 是，服务明确表示暂时不可用 |

重新执行实验 1 的启动命令，继续后面的实验。

## 实验 3：使用真实契约创建工单

```powershell
curl.exe -v `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Authorization: Bearer lab-token-tenant-a" `
  -H "Content-Type: application/json" `
  -H "X-Request-ID: req_lesson_001" `
  --data-raw '{\"title\":\"Cannot-sign-in\"}'
```

关键响应：

```text
< HTTP/1.1 201 Created
< x-request-id: req_lesson_001
{
  "code":"ok",
  "message":"created",
  "request_id":"req_lesson_001",
  "data":{
    "id":"...UUID v4...",
    "tenant_id":"tenant_a",
    "title":"Cannot-sign-in",
    "status":"open",
    "version":1
  }
}
```

请求 Body 只有 `title`。`tenant_id` 来自服务端验证 Token 后得到的可信 `Principal`，不是客户端
自报字段。响应 Header 和 JSON 中的 `request_id` 相同，日志才能沿同一次请求关联。

### 这段 JSON 去了哪里

```text
curl 发送 JSON 字节
-> Uvicorn 接收连接
-> request_context middleware 生成或保留 request ID
-> get_principal 验证教学 Token
-> create_ticket Handler 接收 TicketCreate
-> TicketService.create 创建 Ticket
-> InMemoryTicketRepository.create 保存到内存
-> FastAPI 把 ApiResponse 序列化为 JSON
```

对应文件：

- 路由、中间件、认证：[main.py](../exercises/python-ticket-api/app/main.py)
- 输入与输出模型：[models.py](../exercises/python-ticket-api/app/models.py)
- 业务调用：[service.py](../exercises/python-ticket-api/app/service.py)
- 内存保存：[repository.py](../exercises/python-ticket-api/app/repository.py)

## 实验 4：用同一接口比较失败

以下命令都在服务运行时执行。每次记录：有没有状态码、HTTP 状态码、JSON `code`。

### 缺少 Token：401

```powershell
curl.exe -sS -i `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Content-Type: application/json" `
  --data-raw '{\"title\":\"No-auth\"}'
```

关键结果：`401` 与 `authentication_required`。

### 无效 Token：401

```powershell
curl.exe -sS -i `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Authorization: Bearer invalid-token" `
  -H "Content-Type: application/json" `
  --data-raw '{\"title\":\"Invalid-auth\"}'
```

关键结果仍是 `401 authentication_required`，但 `message` 会说明 bearer token 无效。
缺少凭据和凭据不被接受都属于认证失败；客户端不能依赖可变化的 message 分支处理。

### JSON 被截断：400

```powershell
curl.exe -sS -i `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Authorization: Bearer lab-token-tenant-a" `
  -H "Content-Type: application/json" `
  --data-raw '{\"title\":'
```

关键结果：`400` 与 `invalid_json`。JSON 字节无法解析成完整值。

### 未知字段：422

```powershell
curl.exe -sS -i `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Authorization: Bearer lab-token-tenant-a" `
  -H "Content-Type: application/json" `
  --data-raw '{\"title\":\"Unknown-field\",\"debug\":true}'
```

关键结果：`422 invalid_ticket_input`。JSON 语法正确，但 `StrictInput` 的
`extra="forbid"` 不允许 `debug`。

### 客户端伪造 tenant_id：422

```powershell
curl.exe -sS -i `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Authorization: Bearer lab-token-tenant-a" `
  -H "Content-Type: application/json" `
  --data-raw '{\"title\":\"Forged\",\"tenant_id\":\"tenant_b\"}'
```

关键结果：`422` 与 `invalid_ticket_input`。JSON 合法，但未知业务字段违反输入模型。

### 空白标题：422

```powershell
curl.exe -sS -i `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Authorization: Bearer lab-token-tenant-a" `
  -H "Content-Type: application/json" `
  --data-raw '{\"title\":\"\u0020\u0020\u0020\"}'
```

关键结果：`422` 与 `invalid_ticket_input`。title trim 后为空。

### UUID 格式错误与资源不存在

```powershell
curl.exe -sS -i `
  -H "Authorization: Bearer lab-token-tenant-a" `
  http://127.0.0.1:8000/api/v1/tickets/not-a-uuid
```

结果是 `422 invalid_ticket_input`：Path 不是约定格式。

```powershell
curl.exe -sS -i `
  -H "Authorization: Bearer lab-token-tenant-a" `
  http://127.0.0.1:8000/api/v1/tickets/00000000-0000-4000-8000-000000000001
```

结果是 `404 ticket_not_found`：格式是 UUID v4，但当前租户没有这条工单。

### 500 如何观察

不要为了制造 `500` 随意破坏正在运行的代码。仓库已有一个可恢复的测试替身：

```powershell
cd exercises\python-ticket-api
python -m pytest tests/test_tickets.py -k unexpected_error -v -p no:cacheprovider
```

测试让 Repository 抛出 `RuntimeError`，断言服务返回 `500 internal_error`，同时保留 request ID。

## 引导练习：把观察结果写成代码

打开 [第 1 课实验](../exercises/01-request-lifecycle/README.md)，只修改
`starter/observations.py` 中的两个 TODO。

```powershell
python -m pytest exercises/01-request-lifecycle/tests -v -p no:cacheprovider
```

先看到 3 个 `NotImplementedError`，再最小实现。不要修改测试。

## 独立练习

新建 `progress/lesson-01-observations.md`，记录八次失败实验，格式固定为：

```text
命令：
是否建立连接：
HTTP 状态码（没有则写 none）：
稳定 code（没有则写 none）：
证据中的关键行：
```

验收条件：八条记录覆盖停止服务、缺 Token、无效 Token、非法 JSON、未知字段、
伪造 tenant_id、空白 title 与非法 UUID；另用现有测试记录 500 证据。

## 常见错误与排查

1. `No module named uvicorn`：运行 `python -m pip install -r requirements-repo.lock`，确认当前目录。
2. 端口已占用：用 `Get-NetTCPConnection -LocalPort 8000` 找进程，不要盲目结束未知进程；可改用 8001，并同步修改 curl URL。
3. `curl` 被 PowerShell 映射：显式使用 `curl.exe`。
4. JSON 引号错误：Windows PowerShell 5.1 调用 `curl.exe` 时，外层用单引号，并把传给原生程序的 JSON 双引号写成 `\"`；示例还避免在单个原生参数中放字面空格。
5. 包已安装却无法导入：核对 `python -c "import sys; print(sys.executable)"` 与 `python -m pip --version`。

## 不看代码复述

1. 源文件、进程和监听端口分别是什么？
2. 连接被拒绝或超时为什么没有 HTTP 状态码？
3. `400 invalid_json` 与 `422 invalid_ticket_input` 的边界是什么？
4. 为什么客户端不能提交 `tenant_id`？
5. request ID 为什么同时出现在 Header 和 Body？
6. 创建后重启服务，工单为什么消失？

## 本课总结与下一课

你已经能观察一个请求真实经过当前服务。下一课只学习 Python 如何把外部 JSON 变成受验证的
`TicketCreate`，再变成内部 `Ticket`。PostgreSQL、BFF、事务、幂等和 Outbox 会在它们真正接入
实验时出现，现在只记住：当前 Repository 是进程内存。
