# Lessons：成熟后端知识的长期入口

`lessons/` 放的是已经整理成体系、脱离原聊天上下文也能独立阅读的后端教程。

这里不是要求从 00 一路按编号读到 16。编号只表示大致依赖关系；平时先从真实问题进入，再回到对应 lesson。

如果只是隔几周回来快速恢复记忆，先看 [`../notes/knowledge-map.md`](../notes/knowledge-map.md) 或对应 cheatsheet；如果某个结论只有亲手制造失败才能真正理解，再去 [`../exercises/`](../exercises/) 做实验。

---

## 目录怎么用

| 主题 | Lesson | 最自然的验证入口 |
| --- | --- | --- |
| 学习方法、仓库怎么用 | [`00-start-here.md`](00-start-here.md) | [`../progress/README.md`](../progress/README.md) |
| Windows / Python / Go / Docker 环境 | [`00b-environment-setup.md`](00b-environment-setup.md) | `scripts/check.ps1` |
| 进程、端口、HTTP 请求生命周期 | [`01-request-lifecycle.md`](01-request-lifecycle.md) | [`../exercises/01-request-lifecycle/`](../exercises/01-request-lifecycle/) |
| Python 后端对象、类型、分层基础 | [`02-python-backend-foundations.md`](02-python-backend-foundations.md) | [`../exercises/02-python-backend-foundations/`](../exercises/02-python-backend-foundations/) |
| Handler / Service / Repository | [`03-layered-service.md`](03-layered-service.md) | [`../exercises/03-layered-service/`](../exercises/03-layered-service/) |
| API 契约、strict input、可信 Principal | [`04-api-contracts.md`](04-api-contracts.md) | [`../exercises/04-api-contracts/`](../exercises/04-api-contracts/) |
| SQL、约束、索引、连接与 PostgreSQL | [`05-sql-postgresql.md`](05-sql-postgresql.md) | [`../exercises/sql-postgres/`](../exercises/sql-postgres/) |
| Transaction、锁、并发更新、幂等 | [`06-transactions-idempotency.md`](06-transactions-idempotency.md) | SQL / reliability labs |
| Redis 的角色、缓存、TTL、锁边界 | [`07-redis.md`](07-redis.md) | [`../exercises/redis-lab/`](../exercises/redis-lab/) |
| goroutine / async / timeout / cancel | [`08-concurrency-timeouts.md`](08-concurrency-timeouts.md) | reliability labs + Go tests |
| Outbox、Streams、ACK、Pending、恢复 | [`09-streams-outbox.md`](09-streams-outbox.md) | Redis / PostgreSQL reliability labs |
| Cookie、Session、JWT、鉴权与安全 | [`10-auth-security.md`](10-auth-security.md) | [`../notes/authentication-cheatsheet.md`](../notes/authentication-cheatsheet.md) |
| 测试、代码审查、Debug | [`11-testing-debugging.md`](11-testing-debugging.md) | [`../progress/debug-log.md`](../progress/debug-log.md) |
| Logs、Metrics、Trace、SLO | [`12-observability.md`](12-observability.md) | metrics demo |
| Docker、Image、CI/CD、Kubernetes | [`13-docker-k8s-ci.md`](13-docker-k8s-ci.md) | infrastructure + K8s dry-run |
| 单体/微服务、Gateway、REST/gRPC/Event | [`14-grpc-events-boundaries.md`](14-grpc-events-boundaries.md) | capstone P6（可选） |
| RAG / Agent 的生产后端边界 | [`15-rag-agent-production.md`](15-rag-agent-production.md) | fake RAG / tool authorization |
| 从需求和失败模型推系统设计 | [`16-system-design.md`](16-system-design.md) | capstone + architecture review |

---

## 一篇 Lesson 什么时候算“成熟”

至少应能回答：

```text
这个概念为什么存在？
不用它会出现什么具体问题？
它在请求/数据链的哪一层？
一条正常数据流怎么走？
至少两个真实失败场景是什么？
最小 Demo 证明了什么？
它还没有证明什么生产问题？
关闭文档以后我应该能自己讲什么？
```

只有名词列表、API 罗列或命令集合的内容，不应该被当成成熟 lesson。

---

## 学习时不要追求“全部看完”

更好的循环是：

```text
真实问题
↓
找到当前所在层
↓
读一个相关 Lesson
↓
用自己的话复述
↓
做最小实验 / 看真实代码
↓
制造一个失败
↓
记录能力证据
```

例如遇到：

```text
客户端超时后重试，数据库会不会写两次？
```

不需要先把 Redis、K8s、微服务读完，直接进入第 6 课的 transaction / idempotency。

---

## 代码语言不是知识边界

同一个概念可以在不同语言里复现：

```text
HTTP middleware
Go -> net/http
Python -> FastAPI middleware/dependency

Cancellation
Go -> context.Context
Python -> asyncio task / timeout
```

学习目标是先掌握后端语义，再掌握语言实现方式。

---

## Lesson 和 Learning Journal 的区别

`notes/learning-journal/` 保存一次具体学习过程里纠正的重要误区。

`lessons/` 保存已经抽象成通用教程的知识。

所以不要把每次聊天都升级成 lesson，也不要让成熟知识永远只散落在 journal。

长期维护原则见 [`../AGENTS.md`](../AGENTS.md)。
