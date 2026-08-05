# 第 3 课：让失败测试推动 Handler、Service、Repository 分开

预计用时：70～90 分钟。实验数量：3 个主实验、2 个故障实验、5 个失败测试。

## 你将亲手完成什么

- 运行一个故意把协议、规则和存储混在一起的函数；
- 观察全局状态为什么让测试相互影响；
- 不启动 HTTP 服务，先用 Service 测试描述关闭工单规则；
- 把状态与版本规则移入 Service，把存取移入 Repository；
- 解释 Handler、Service、Repository 各自应该知道和不应该知道什么。

## 前置条件与当前状态

你已理解 `TicketCreate`、`Ticket`、`async/await` 和 Protocol。打开
[第 3 课实验](../exercises/03-layered-service/README.md)：

```text
starter/api.py          故意写坏的 all-in-one Handler
starter/models.py       已解析的 close 输入
starter/repository.py   可替换的内存存储
starter/service.py      保留 TODO 的业务用例
tests/test_service.py   不启动 HTTP 的验收
```

## 本课不讲什么

本课不连接 PostgreSQL，也不讲数据库事务、HTTP 部署或 Go。这里先建立可测试边界。

## 实验 1：运行 all-in-one Handler

在仓库根目录运行：

```powershell
python -c "from pathlib import Path; import sys; sys.path.insert(0, str(Path('exercises/03-layered-service'))); from starter.api import close_ticket; print(close_ticket('ticket-1', {'expected_version': 1})); print(close_ticket('ticket-1', {'expected_version': 2})); print(close_ticket('ticket-1', {'expected_version': 1}, tenant_id='tenant_b'))"
```

关键输出：

```text
{'status': 200, 'code': 'ok', 'data': {'tenant_id': 'tenant_a', 'status': 'closed', 'version': 2}}
{'status': 409, 'code': 'ticket_state_conflict'}
{'status': 404, 'code': 'ticket_not_found'}
```

函数看起来能工作，但一口气做了五件事：

1. 把字典解析成 `CloseTicket`；
2. 从全局 `TICKETS` 查找状态；
3. 判断不存在、状态和版本；
4. 修改全局字典；
5. 决定 HTTP 状态码与错误码。

### 故障实验：测试顺序改变状态

在同一个 Python 进程中第一次调用已把 `ticket-1` 改成 closed。第二个测试若假设它仍是 open，
就会受前一个测试影响。重新执行整个 `python -c` 命令时进程重启，全局字典恢复。

这证明“代码短”不等于“边界清楚”。问题不是字典本身，而是协议、业务和共享状态无法独立替换。

用自动化测试重现同一问题：

```powershell
python -m pytest exercises/03-layered-service/tests/test_all_in_one.py -v -p no:cacheprovider
```

预计 `1 passed`。通过不是说坏设计已经修好，而是测试稳定证明：第一次调用修改了全局字典，
第二次调用会观察到前一次留下的 closed 状态。

## 实验 2：先写 Service 的期望

Service 测试不关心 HTTP `409`，只关心业务结果：

```text
tenant_a + open + expected_version=1 -> closed, version=2
missing -> TicketNotFound
tenant_b reads tenant_a ticket -> TicketNotFound
current version != expected -> TicketVersionConflict
already closed -> TicketStateConflict
```

运行：

```powershell
python -m pytest exercises/03-layered-service/tests -v -p no:cacheprovider
```

起始结果应为 `5 failed, 1 passed`。通过项固定了 all-in-one Handler 的状态污染现象；
5 个失败点都是 `TicketService.close` 的 `NotImplementedError`。这是有价值的
失败：测试已经表达“应该做什么”，而实现尚未完成。

测试为每个用例新建 `InMemoryTicketRepository()`，不共享状态；也没有 Uvicorn、端口、Token 或 JSON。
因此失败能直接指向业务规则。

## 实验 3：按职责完成最小实现

只修改 `starter/service.py`。每完成一个行为就运行对应测试：

```powershell
python -m pytest exercises/03-layered-service/tests -k close_moves -v -p no:cacheprovider
python -m pytest exercises/03-layered-service/tests -k missing -v -p no:cacheprovider
python -m pytest exercises/03-layered-service/tests -k stale -v -p no:cacheprovider
python -m pytest exercises/03-layered-service/tests -k duplicate -v -p no:cacheprovider
python -m pytest exercises/03-layered-service/tests -k cross_tenant -v -p no:cacheprovider
```

不要批量写完再猜哪里错。实现顺序由失败测试决定：

```text
await Repository.get(tenant_id, ticket_id)
-> 不存在则抛业务异常
-> 已关闭则抛状态冲突
-> 版本不等则抛版本冲突
-> 创建更新后的状态
-> await Repository.save(tenant_id, ticket_id, ticket)
-> 返回领域结果
```

最终命令：

```powershell
python -m pytest exercises/03-layered-service/tests -v -p no:cacheprovider
```

预计：`6 passed`，其中 1 个是改造前现象测试，5 个是 Service 验收。

## 分层后的数据流

```text
Handler
  接收协议输入，调用 Service，把领域错误翻译成 HTTP
    -> Service
       执行 close 用例与状态/版本规则
         -> Repository
            获取和保存状态，不返回 HTTP 404/409
```

| 层 | 知道什么 | 不应该知道什么 |
| --- | --- | --- |
| Handler | Method、Path、JSON、Principal、HTTP 响应 | 存储字典、SQL、状态迁移细节 |
| Service | 用例、状态规则、领域错误、可信 tenant_id | FastAPI Request、HTTP 状态码 |
| Repository | 按租户获取/保存、并发写入结果 | 谁能关闭、返回哪个 HTTP code |
| Model | 字段与不变量 | 端口、环境变量、数据库连接 |

### 依赖方向

Service 构造时接收 `TicketRepository`，而不是自己创建具体存储：

```python
service = TicketService(InMemoryTicketRepository())
```

以后换 PostgreSQL 时，Service 的业务测试不应该整体重写。这是引入抽象的原因，而不是为了文件数量。

## 故障实验：把 HTTP 泄漏进 Service

假设 Service 返回：

```python
{"status": 409, "code": "ticket_state_conflict"}
```

那么命令行任务、事件消费者或另一个协议调用同一 Service 时也被迫理解 HTTP。正确做法是 Service
抛 `TicketStateConflict`，由当前入口决定如何表示。不要真的修改 starter；在笔记中写出这两种调用方
各自可能采用的表示方式。

## 引导练习

完成 [starter/service.py](../exercises/03-layered-service/starter/service.py) 的 TODO。限制：

- 不导入 `api.py`；
- 不访问全局 `TICKETS`；
- 不返回 HTTP 状态码；
- 每个 Repository 操作都使用 `await`；
- 不修改测试。

卡住时使用[三级提示](../exercises/03-layered-service/hints.md)。

## 独立练习

完成后，在 `progress` 中写一张表：对 `close_ticket` 的每一行判断它属于协议、业务还是存储。
再回答：如果 Repository 的 `save` 抛出异常，哪个层应该记录技术错误，哪个层不应该把它伪装成
`TicketNotFound`？

## 常见错误与排查

1. 测试互相污染：是否复用了同一个 Repository 实例？
2. duplicate 测试没有冲突：第一次保存的 closed 状态是否真的写回？
3. stale 与 state 冲突顺序不同：先确定契约要求，本练习先检查状态再检查版本。
4. 忘记 await：得到 coroutine object，Repository 操作没有完成。
5. Service 返回字典中的 `status=409`：HTTP 语义仍未抽离。

## 不看代码复述

1. all-in-one Handler 为什么难以做确定性测试？
2. Service 测试为什么不需要启动 Uvicorn？
3. Repository 为什么不决定 `409`？
4. Protocol 是在哪个具体替换需求出现后才有价值？
5. 如果接入 PostgreSQL，事务、索引、租户过滤和失败恢复应在哪一层讨论？

## 下一课为什么需要出现

现在单个 Python 实现内部边界清楚了，但客户端仍需要知道精确字段、错误码与身份规则。下一课把这些
约定放进机器可读契约，并证明 Python 测试确实读取它，而不是只在文档里说“一致”。
