# 实验索引：用运行结果把“听懂”变成“真的会”

`exercises/` 不是另一套课程，也不是要求按目录顺序全部做完。它只做一件事：把那些**只靠阅读很容易产生错觉**的后端知识，变成可以运行、制造失败、留下证据的最小实验。

使用方式：

```text
对话/课程先讲懂概念
        ↓
选择一个最小实验
        ↓
先运行原始失败或基线
        ↓
只改允许的范围
        ↓
再次运行并解释结果
        ↓
把结论写进 progress 或 learning-journal
```

## 实验地图

| 目录 | 主要证明什么 | 什么时候做 |
| --- | --- | --- |
| `01-request-lifecycle/` | 网络错误、HTTP 错误、request ID 不是同一层 | 学 HTTP 请求生命周期时 |
| `02-python-backend-foundations/` | 输入模型、领域状态和默认值如何一致传播 | 学 Python API 模型时 |
| `03-layered-service/` | Handler / Service / Repository 为什么要分层 | 能写 Handler 但职责还混乱时 |
| `04-api-contracts/` | 人读文档和机器契约如何共同守住行为 | 学 strict JSON / contract test 时 |
| `python-ticket-api/` | 一套可运行的 Python 分层 HTTP 基线 | 需要观察完整请求链时 |
| `go-ticket-api/` | 用 Go `net/http` 复现同一后端概念 | 当前以 Go 为主时 |
| `infrastructure/` | Docker Compose、PostgreSQL、Redis 的本地运行边界 | 真正需要外部依赖后 |
| `sql-postgres/` | constraint、index、transaction、Outbox | 学 PostgreSQL 时 |
| `redis-lab/` | Cache Aside、Streams、Pending、reclaim | 已经明确 Redis 角色时 |
| `reliability-labs/` | timeout、auth、Webhook、Outbox、RAG、metrics 等故障微实验 | 需要验证生产失败模式时 |

## 每个实验都按这 6 个问题验收

1. **它要证明什么不变量？** 不能只说“测试通过”。
2. **原始失败是什么？** 如果没有失败/基线，你很难知道修改证明了什么。
3. **你允许改哪里？** 避免同时改测试、契约和实现把问题掩盖掉。
4. **通过意味着什么？** 例如 unit test 通过不等于数据库/网络行为已经验证。
5. **还有什么没证明？** Demo、内存 fake、单进程和生产系统边界要明确。
6. **关闭文档后能不能解释？** 至少能画出输入、状态变化、输出和一个失败窗口。

## 不要这样使用实验

```text
复制最终代码
→ 看到 green
→ 下一章
```

也不要因为某个目录出现 Redis/K8s/Agent 就提前全部启动。只有当当前问题真的需要那个组件时再进入相应实验。

## 证据怎么记录

最小记录：

```text
日期：
实验：
我原来以为：
基线/失败：
我修改：
最终结果：
这个结果证明：
仍未证明：
```

长期能力等级写到 [`../progress/README.md`](../progress/README.md)，真实 Debug 过程写到 [`../progress/debug-log.md`](../progress/debug-log.md)。
