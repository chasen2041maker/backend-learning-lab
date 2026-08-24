# 第 4 课实验：让机器契约自己回答“系统应该怎样表现”

先阅读 [`lessons/04-api-contracts.md`](../../lessons/04-api-contracts.md)。本练习不修改 API，而是读取真实的 [`contracts/http-cases.json`](../../contracts/http-cases.json)。目标不是练 JSON 语法，而是建立一个重要习惯：

> **当两个实现、多个客户端或长期维护都依赖同一行为时，不要只靠自然语言记忆契约。**

## 人读文档和机器契约分别做什么

```text
api-contract.md
→ 解释为什么、语义、示例、兼容性

http-cases.json
→ 给测试程序稳定读取的关键行为样例
```

机器用例重点覆盖：

- strict JSON；
- `400 invalid_json` 与 `422 invalid_ticket_input` 的分界；
- UUID 文本/版本边界；
- tenant 身份来源；
- 跨租户隐藏 404；
- version conflict；
- list limit 等边界。

## 允许修改的范围

只修改：

```text
starter/contract_reader.py
```

禁止：

- 硬编码当前用例名称；
- 修改 `http-cases.json` 迎合错误实现；
- 排序结果改变契约原顺序；
- 把不是 list 的 section 默默当空列表。

## 第一步：跑失败

```powershell
python -m pytest exercises/04-api-contracts/tests -v -p no:cacheprovider
```

预计 3 个测试因 `NotImplementedError` 失败。

先读测试，回答：它是在验证“某个 API 实现”，还是在验证“我们能正确读取共享契约”？

## 完成后你应该真正理解

### 1. 契约不是实现

Python 和 Go 可以完全不同，但对外：

```text
相同输入
→ 相同关键 status/code/shape
```

### 2. 不要根据错误 message 写客户端分支

稳定的是：

```text
expected_code
```

文案可以改、可以本地化。

### 3. 机器文件也需要 schema/结构保护

如果 section 从 list 意外改成 object，而 reader 默默返回空结果，测试可能失去覆盖却没人发现。因此结构错误应该显式失败。

## 通过后的证据

```powershell
python -m pytest exercises/04-api-contracts/tests -v -p no:cacheprovider
python scripts/validate_contracts.py
```

然后关闭文档回答：

1. 为什么 Markdown 契约不能完全替代机器用例？
2. 为什么机器用例也不能完全替代解释性文档？
3. 什么叫 contract drift？
4. 为什么“只改测试让它过”可能掩盖 breaking change？
5. 如果新增可选响应字段，通常是否一定 breaking？如果删除现有字段呢？

## 故障实验

在临时分支中把一个契约 section 改成错误类型，运行 reader tests/validation，确认系统会明确失败；随后恢复契约。

卡住时按顺序查看 [`hints.md`](hints.md)。
