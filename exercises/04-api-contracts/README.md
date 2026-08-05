# 第 4 课实验：让机器契约回答问题

先阅读[第 4 课正文](../../lessons/04-api-contracts.md)。本练习不修改 API，只读取真实的
`contracts/http-cases.json`，从机器用例中找 strict input、跨租户隐藏和 invalid JSON 边界。

先运行：

```powershell
python -m pytest exercises/04-api-contracts/tests -v -p no:cacheprovider
```

预计 3 个测试因 `NotImplementedError` 失败。只修改 `starter/contract_reader.py`，不要硬编码用例名，
也不要修改契约文件来迎合测试。

卡住时按顺序查看 [hints.md](hints.md)。
