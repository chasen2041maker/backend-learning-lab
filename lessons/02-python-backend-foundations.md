# 第 2 课：Python 如何表达后端输入、状态与依赖

预计用时：75～90 分钟。实验数量：5 个主实验、2 个故障实验、1 组失败测试。

## 你将亲手完成什么

完成本课后，你能够：

- 区分外部输入 `TicketCreate`、内部状态 `Ticket` 和输出 `ApiResponse[Ticket]`；
- 运行 strict validation，观察 trim、Unicode 长度和未知字段错误；
- 沿 `Handler -> Service -> Repository` 跟踪一次创建调用；
- 解释 `async def` 创建协程、`await` 等待异步操作的含义；
- 先运行失败测试，再为缩小版 starter 增加 priority；
- 说明 Protocol 为什么在测试替身出现后才有价值。

本课只讲 Python。Go 会在第 8～9 周复现已经理解的概念，不在同一天学习新语言和新后端边界。

## 本课不讲什么

不连接数据库，不实现生产认证，不修改 Go，也不让学习者直接改成品 API。priority 只在独立
starter 中完成，先把 Python 输入、状态和依赖讲清楚。

## 前置条件和起始状态

你已完成第 1 课，能启动服务和识别 `400`、`401`、`404`、`422`。在仓库根目录执行：

```powershell
python --version
python -c "import pydantic, pytest, pytest_asyncio; print('lesson 2 ready')"
```

关键输出：

```text
lesson 2 ready
```

本课主要阅读成品项目的四个文件：

- [models.py](../exercises/python-ticket-api/app/models.py)
- [service.py](../exercises/python-ticket-api/app/service.py)
- [repository.py](../exercises/python-ticket-api/app/repository.py)
- [main.py](../exercises/python-ticket-api/app/main.py)

挑战在独立的 [第 2 课 starter](../exercises/02-python-backend-foundations/README.md) 中完成，避免在理解前改坏成品 API。

## 实验 1：输入模型拒绝什么

从仓库根目录启动 Python 交互模式：

```powershell
python
```

逐段输入，不要一次粘贴全部：

```python
from app.models import TicketCreate
```

如果当前目录无法导入 `app`，先执行：

```powershell
cd exercises\python-ticket-api
python
```

### 合法输入与 trim

```python
command = TicketCreate(title="  Cannot sign in  ")
command
command.title
```

关键输出：

```text
TicketCreate(title='Cannot sign in')
'Cannot sign in'
```

数据先经过 `field_validator(..., mode="before")`。validator 确认原值确实是字符串并执行
`strip()`，然后 Pydantic 才检查长度 1～200。顺序很重要：两侧空格不应占 title 长度。

### 故障实验 1：strict validation 拒绝数字

```python
TicketCreate(title=123)
```

关键错误包含：

```text
Value error, title must be a string
```

`strict=True` 的目的不是“更高级”，而是避免客户端发送数字、布尔值后被悄悄转换成字符串或整数。

### 未知字段与可信租户

```python
TicketCreate(title="Forged", tenant_id="tenant_b")
```

关键错误：

```text
Extra inputs are not permitted
```

`extra="forbid"` 让拼错或伪造字段立即失败。`tenant_id` 不属于 `TicketCreate`，它由认证产生的
`Principal` 提供。

### trim 后 Unicode 长度

```python
len(TicketCreate(title=" " + "中" * 200 + " ").title)
TicketCreate(title="中" * 201)
```

第一条输出 `200`；第二条错误包含“at most 200 characters”。这里按 Python Unicode 字符计数，
不是按 UTF-8 字节计数。

输入 `exit()` 退出交互模式。

## 三种模型不是一回事

### TicketCreate：外部输入

它只包含客户端允许提交的字段，并负责把不可信 JSON 拦在业务逻辑之前。

### Ticket：内部领域状态

`Ticket` 包含服务端生成的 `id`、可信 `tenant_id`、状态、版本和时间。客户端不能决定这些字段。

```text
TicketCreate(title)
          + Principal.tenant_id
          + 服务端生成的 UUID/time/status/version
          -> Ticket
```

`Ticket.new(command, tenant_id)` 是状态创建点。新工单在这里获得 `open` 和 `version=1`。

### ApiResponse[Ticket]：外部输出

`ApiResponse` 包装稳定 `code`、人类可读 `message`、`request_id` 和业务 `data`。泛型参数
`Ticket` 表示本次 `data` 的类型，便于 FastAPI 生成文档并校验输出。

## 实验 2：函数、类型提示和错误

查看 `TicketService.create`：

```python
async def create(self, tenant_id: str, command: TicketCreate) -> Ticket:
    ticket = Ticket.new(command, tenant_id)
    return await self._repository.create(ticket)
```

类型提示说明预期输入输出，但 Python 不会因为写了 `str` 就自动验证任意运行时对象。外部 HTTP
输入由 Pydantic 验证，Service 则接收已经验证的数据和可信租户。

`DomainError` 是可预期业务失败的基类，例如 `TicketNotFound`。Handler 把它翻译成稳定 HTTP
响应。未预期的 `RuntimeError` 不应伪装成“工单不存在”，而应进入 500 处理和日志。

运行现有错误测试：

```powershell
cd exercises\python-ticket-api
python -m pytest tests/test_tickets.py -k "blank_title or unexpected_error" -v -p no:cacheprovider
```

关键结果：

```text
2 passed
```

一个测试证明可预期验证错误是 `422 invalid_ticket_input`；另一个让 Repository 抛异常，证明
未知错误是 `500 internal_error` 且 request ID 不丢失。

## 实验 3：async/await 到底在等待什么

在仓库根目录打开交互模式：

```powershell
python
```

```python
import asyncio

async def store_ticket() -> str:
    await asyncio.sleep(0.01)
    return "stored"

asyncio.run(store_ticket())
```

输出：

```text
'stored'
```

- 调用 `store_ticket()` 先得到协程对象，不会自动完成函数；
- `asyncio.run` 启动事件循环；
- `await asyncio.sleep(...)` 表示当前协程等待，同时允许事件循环运行其他任务；
- 在 Repository 中，`await` 将来通常等待网络数据库 I/O；当前内存 Repository 没有真实网络等待，
  但保留相同接口让 Service 不必因存储实现变化而重写。

### 故障实验 2：忘记 await

在交互模式输入但不 await：

```python
result = store_ticket()
result
```

输出是 `<coroutine object ...>`，不是字符串。关闭解释器时还可能看到“coroutine was never awaited”警告。

## 实验 4：asyncio.Lock 保护哪一段

当前真实的内存 Repository 在构造函数中创建 `asyncio.Lock`，每个读写方法用
`async with self._lock` 包住字典访问。先观察对象类型：

```powershell
python -c "from app.repository import InMemoryTicketRepository; print(type(InMemoryTicketRepository()._lock).__name__)"
```

预计输出：

```text
Lock
```

这个锁只保护当前进程里的 `_tickets` 字典，避免两个协程同时修改同一份内存状态；
它不是跨进程、跨机器的数据库锁。将来换成 PostgreSQL 时，事务和数据库锁会承担不同的
一致性职责，本课只观察现有内存实现。

## 实验 5：为什么 Repository Protocol 现在才出现

如果 Service 自己维护全局字典，它同时负责业务规则和存储细节。测试无法替换失败存储，也难以证明
Service 传给存储的对象是什么。

`TicketRepository(Protocol)` 只描述 Service 真正需要的操作：

```python
class TicketRepository(Protocol):
    async def create(self, ticket: Ticket) -> Ticket: ...
```

Service 构造时从外部接收依赖：

```python
service = TicketService(InMemoryTicketRepository())
```

这叫依赖注入。Protocol 的价值不是多建文件，而是允许另一种满足同一操作形状的实现被传入。

运行一个最小调用：

```powershell
python -c "import asyncio; from app.models import TicketCreate; from app.repository import InMemoryTicketRepository; from app.service import TicketService; print(asyncio.run(TicketService(InMemoryTicketRepository()).create('tenant_a', TicketCreate(title='Demo'))))"
```

在 `exercises/python-ticket-api` 目录执行。关键输出包含：

```text
tenant_id='tenant_a' title='Demo' status=<TicketStatus.OPEN: 'open'> version=1
```

调用顺序：

```text
调用者构造 TicketCreate
-> TicketService.create 接收可信 tenant_id 与 command
-> Ticket.new 创建全部内部状态
-> await repository.create(ticket)
-> Repository 保存并返回 Ticket
-> Service 把 Ticket 返回给 Handler
-> Handler 包装 ApiResponse
```

## 引导练习：先失败，再增加 priority

进入[第 2 课实验](../exercises/02-python-backend-foundations/README.md)，先运行：

```powershell
python -m pytest exercises/02-python-backend-foundations/tests -v -p no:cacheprovider
```

起始状态应为 5 failed、2 passed。已通过的是两个非法 priority 测试，因为它目前仍是未知字段；
其中 HTTP 测试还证明 FastAPI 把 Pydantic 验证失败翻译为 422。失败测试
要求你把它变成正式字段，同时保持只接受 `low`、`normal`、`high`。

只修改 `starter/models.py` 的 TODO。目标：

1. `TicketCreate` 未传 priority 时为 `normal`；
2. 三个允许值能穿过 Service 和 Repository；
3. `urgent` 仍由 Pydantic 拒绝；
4. `Ticket` 和 `ApiResponse` 输出 priority；
5. 非法 priority 通过最小 FastAPI 入口返回 422；
6. 全部 7 个测试通过。

不要从本课正文复制最终实现；卡住时每次只看 [一级提示](../exercises/02-python-backend-foundations/hints.md)。

最后执行静态验收：

```powershell
python -m ruff check exercises/02-python-backend-foundations
```

预计输出：`All checks passed!`。

## 独立练习

完成测试后，关闭编辑器中的提示文件，在纸上或 `progress` 中写出：

```text
外部 JSON 的 priority 在哪里首次验证？
默认值在哪里产生？
哪个函数把它复制进 Ticket？
Repository 收到的对象有什么字段？
响应 JSON 为什么自动出现 priority？
```

然后删除自己对 starter 的实现，第二天只看测试重做一次。Git 能恢复已提交文件，但在你自己的未提交
练习中先保留答案副本再删除，避免误删其他工作。

## 常见错误与排查

1. `Extra inputs are not permitted`：priority 还没加入 `TicketCreate`。
2. `Ticket has no attribute priority`：只改了输入，内部状态还没有字段。
3. 默认测试通过、显式值丢失：检查 `Ticket.new()` 是否从 `command` 复制。
4. `urgent` 被接受：字段类型过宽，有限集合没有进入 Pydantic schema。
5. async 测试被跳过：确认安装 `pytest-asyncio`，并保留 `@pytest.mark.asyncio`。

## 不看代码复述

1. `TicketCreate`、`Ticket`、`ApiResponse[Ticket]` 分别属于哪一侧边界？
2. strict validation 防止了哪类静默转换？
3. 为什么 title 要先 trim 再检查长度？
4. tenant_id 从哪里来，为什么不在输入模型里？
5. `await repository.create(...)` 将来可能等待什么？
6. 什么时候引入 Protocol 有价值，什么时候只是增加文件？

## 本课总结与下一课

本课从输入、状态、输出和依赖理解了现有分层，但直接看成品仍看不到“为什么需要分层”。下一课会从
一个难测试的 Handler 开始，先写失败测试，再逐步抽出 Service 和 Repository。Go 只会在第 8～9 周
复现这些已经掌握的概念。
