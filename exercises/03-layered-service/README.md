# 第 3 课实验：从 all-in-one Handler 抽出真正的 Service 边界

先阅读 [`lessons/03-layered-service.md`](../../lessons/03-layered-service.md)。`starter/api.py` 故意把输入解析、业务状态规则、存储和响应混在一个函数里；你不是为了“代码更漂亮”而分层，而是要证明：

> **业务规则应该能脱离 HTTP 独立测试，存储实现也不应该决定业务语义。**

## 先看坏结构会造成什么

all-in-one Handler 容易出现：

```text
HTTP status 决定业务逻辑
全局状态泄漏到测试之间
跨租户检查散落在路由代码
Repository 错误直接变成客户端文案
状态机规则无法脱离 Web Server 测试
```

所以目标调用链是：

```text
Handler
  ↓  已验证的命令 + Principal
Service
  ↓  业务规则
Repository
  ↓  数据读写
```

## 允许修改的范围

只修改：

```text
starter/service.py
```

不要让 Service 返回 HTTP status；不要修改 tests；不要通过改全局变量绕过失败。

## 第一步：保留原始失败

```powershell
python -m pytest exercises/03-layered-service/tests -v -p no:cacheprovider
```

基线预计：

```text
5 failed, 1 passed
```

那个已经通过的测试不是“好消息”，它用于暴露坏 Handler 的全局状态问题。读懂它为什么通过。

## 5 个 Service 场景分别证明什么

1. **成功关闭**：合法状态变化发生在 Service。
2. **不存在**：Service 使用领域错误表达“事实不存在”，而不是 HTTP 404。
3. **旧版本**：并发冲突是业务/一致性语义，不是 Handler 的 if。
4. **重复关闭**：状态机必须拒绝非法 transition。
5. **跨租户隐藏**：可信 tenant 进入数据访问/业务边界，客户端不能靠换 ID 越权。

完成后再次运行，预计：

```text
6 passed
```

## 通过以后再解释

- Handler 应负责哪些 HTTP 细节？
- Service 为什么不应该 import FastAPI/HTTP status？
- Repository 应该知道“403”吗？
- 如果把内存 Repository 换成 PostgreSQL，哪一层最应该保持不变？
- 为什么跨租户检查不能只在前端做？

## 故意改坏一次

临时让 Service 在 close 时忽略 `expected_version`，观察版本冲突测试如何失败。恢复以后再运行。

这个实验最终不是为了得到一个分层模板，而是让你能判断：**某条规则到底属于协议、业务还是持久化边界。**

卡住时按顺序查看 [`hints.md`](hints.md)。
