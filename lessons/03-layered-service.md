# 第 3 课：Handler、Service、Repository 为什么要分开

## 四层职责

| 层 | 负责 | 不应该负责 |
| --- | --- | --- |
| Handler/API | HTTP/JSON、状态码、身份输入 | 拼 SQL、决定复杂业务状态 |
| Service | 用例、业务规则、事务意图 | 依赖具体 HTTP 框架 |
| Repository | 查询、写入、锁和数据库错误翻译 | 决定谁有权限关闭工单 |
| Domain/Model | 状态、不变量、值对象 | 连接数据库或读取环境变量 |

## 创建工单的数据流

```text
JSON
→ Handler 验证协议字段
→ Service 校验业务规则
→ Repository 持久化
→ Service 返回领域结果
→ Handler 转换为 HTTP 响应
```

## 常见坏味道

- Handler 中出现几十行 SQL；
- Repository 返回 HTTP 404；
- Service 直接读取全局 Request；
- 一个 2,000 行文件同时处理路由、模型调用、数据库和日志；
- 为每张表机械创建一层，但没有任何业务边界。

分层不是文件越多越好。一个小功能可以很小，但边界要清楚。

## 依赖注入

依赖注入只是“从外部把依赖交给对象”，不是必须使用大型框架：

```python
service = TicketService(repository=InMemoryTicketRepository())
```

```go
service := ticket.NewService(repository)
```

## 练习

实现关闭工单：

- 只有 `open` 可以变成 `closed`；
- 已关闭再次关闭返回稳定冲突；
- 不存在返回 not found；
- Service 测试不启动 HTTP；
- Handler 测试检查状态码和响应体。
