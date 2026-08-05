# 第 2 课实验：用失败测试增加 priority

先阅读[第 2 课正文](../../lessons/02-python-backend-foundations.md)。本目录是一套缩小的
Python 模型和一个最小 FastAPI 入口，不要求修改成品 API。

调用链是：

```text
TicketCreate -> TicketService.create -> Ticket.new -> TicketRepository.create
```

只修改 `starter/models.py` 中标出的 TODO。不要修改测试，也不要提前修改成品项目。

第一次运行：

```powershell
python -m pytest exercises/02-python-backend-foundations/tests -v -p no:cacheprovider
```

预计测试在收集或访问 `priority` 时失败。完成后必须满足：

- 未传 priority 时为 `normal`；
- 只接受 `low`、`normal`、`high`；
- 非法值由 Pydantic 拒绝；
- 通过最小 HTTP 入口提交非法值时返回 422；
- `Ticket` 与 `ApiResponse` 的输出包含 priority；
- 全部 7 个测试通过；
- `python -m ruff check exercises/02-python-backend-foundations` 通过。

卡住时依次查看 [hints.md](hints.md)，每次只看一级。
