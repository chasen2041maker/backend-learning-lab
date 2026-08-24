# 第 2 课实验：让 `priority` 从输入一路成为可靠内部状态

先阅读 [`lessons/02-python-backend-foundations.md`](../../lessons/02-python-backend-foundations.md)。这个练习看起来只是“加一个字段”，真正要学的是：

> **一个外部输入字段进入系统后，验证、默认值、领域对象和 API 输出必须保持一致。**

调用链：

```text
HTTP JSON
  ↓
TicketCreate
  ↓
TicketService.create
  ↓
Ticket.new
  ↓
Ticket
  ↓
Repository
  ↓
ApiResponse
```

## 为什么这个小练习值得做

最常见的真实 bug 不是不会写字段，而是只改了一层：

```text
Request 已经有 priority
但 Ticket.new() 忘记复制
→ 用户传 high，系统内部却变回 normal
```

或者：

```text
内部支持 high
但输入没有枚举约束
→ arbitrary string 流入业务
```

本实验就是用失败测试把这种“字段传播漂移”暴露出来。

## 允许修改的范围

只修改：

```text
starter/models.py
```

不要修改 Service、Repository、API 或测试。限制修改面本身就是练习的一部分：你要判断这个需求真正属于哪一层。

## 第一步：跑基线

```powershell
python -m pytest exercises/02-python-backend-foundations/tests -v -p no:cacheprovider
```

先看每个失败在证明什么，不要直接搜索答案。

## 完成后必须满足

- 未传 `priority` 时默认 `normal`；
- 只接受 `low | normal | high`；
- 非法值在输入模型阶段被拒绝；
- 最小 HTTP 入口提交非法值返回 422；
- `Ticket` 内部状态保留用户选择；
- `ApiResponse` 能看到该字段；
- 7 个测试全部通过。

如果环境安装了 Ruff，再运行：

```powershell
python -m ruff check exercises/02-python-backend-foundations
```

## 通过以后再问自己

1. 默认值应该放在外部输入模型、领域对象，还是两边都明确？为什么？
2. `Literal` 解决的是类型/取值边界，还是完整业务规则？
3. 如果以后 priority 需要根据用户套餐动态决定，继续塞在 Pydantic 类型里合理吗？
4. 为什么这个练习不需要修改 Repository？

## 故意制造一个漂移

完成后临时删除 `Ticket.new()` 对 priority 的复制，再跑测试。你应该能看到：输入验证仍然可能通过，但内部状态已经错误。

这就是本实验真正要留下的心智模型：

```text
外部 schema 正确
≠
内部状态一定正确
```

卡住时按顺序查看 [`hints.md`](hints.md)，一次只看一级。
