# 第 3 课实验：从 all-in-one Handler 抽出 Service

先阅读[第 3 课正文](../../lessons/03-layered-service.md)。`starter/api.py` 故意把输入、状态规则、
存储和响应混在一个函数里；`starter/service.py` 保留唯一 TODO。

先运行：

```powershell
python -m pytest exercises/03-layered-service/tests -v -p no:cacheprovider
```

预计结果是 `5 failed, 1 passed`：通过项证明坏 Handler 会泄漏全局状态，5 个 Service 测试
都因 `NotImplementedError` 失败。只修改 `starter/service.py`，依次让成功关闭、
不存在、旧版本、重复关闭和跨租户隐藏通过。不要让 Service 返回 HTTP 状态码。

完成后再次运行同一命令，预计 `6 passed`。

卡住时按顺序查看 [hints.md](hints.md)。
