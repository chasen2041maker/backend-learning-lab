# 第 1 课实验：记录一次真实请求

本目录不是另一套 Web 服务。先按[第 1 课正文](../../lessons/01-request-lifecycle.md)
运行现有 Python Ticket API，再把观察结果整理成两个小函数。

起始文件：`starter/observations.py`。其中两个 TODO 分别处理：

- 没有 HTTP 响应的网络错误；
- 已收到 HTTP 响应时的稳定业务错误码；
- Header 与 JSON Body 中的 request ID 是否一致。

先运行并保留失败：

```powershell
python -m pytest exercises/01-request-lifecycle/tests -v -p no:cacheprovider
```

预计首先看到 `NotImplementedError`。完成两个 TODO 后再次运行，预计看到：

```text
3 passed
```

不要修改测试来制造通过。卡住时依次查看 [hints.md](hints.md)，一次只看一级。
