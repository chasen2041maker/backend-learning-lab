# Python + Go 后端同步学习路线

建议每天 60～90 分钟。计划按 16 周设计，但不是截止日期；每周只有在完成“独立验收”后才进入下一周。

## 第 0 周：环境与学习方法

- 认识进程、端口、环境变量、依赖和 Git；
- 安装 Python 3.11+、Go 1.22+、Git；
- Docker Desktop 可以延后到第 5 周；
- 分别跑通 Python 和 Go 测试。

验收：关闭教程后，能说明源代码、运行进程、端口和依赖之间的关系。

## 第 1 周：请求生命周期与 HTTP

- 客户端、DNS、TCP、HTTP、反向代理、BFF、服务和数据库；
- 方法、路径、Header、Body、状态码；
- 超时发生在哪一层；
- request ID 为什么要贯穿链路。

验收：画出 `POST /tickets` 从请求到落库再到响应的路径，并标出至少三个失败点。

## 第 2 周：Python 与 Go 的后端基础

- Python 类型提示、异常、上下文管理、`async/await`；
- Go struct、interface、error、`context.Context`、goroutine；
- 两种语言如何表达同一个 Ticket 模型和 Service 接口。

验收：不用 AI 新增一个 `priority` 字段，并修复全部测试。

## 第 3 周：分层服务与依赖注入

- Handler/API：协议翻译；
- Service：业务规则与事务意图；
- Repository：持久化；
- Domain：业务状态和不变量；
- 为什么不能让 Handler 直接拼 SQL。

验收：分别在 Python、Go 项目新增“关闭工单”功能，并证明非法状态转换会失败。

## 第 4 周：API 契约

- REST 资源、版本、统一响应、稳定错误码；
- OpenAPI、分页、兼容变更；
- 身份传播和服务端可信边界；
- 契约测试与实现同步。

验收：先修改 `contracts/api-contract.md`，再修改实现和测试，不允许反过来猜字段。

## 第 5 周：SQL 与 PostgreSQL

- 表、行、主键、外键、唯一约束、检查约束；
- `SELECT/INSERT/UPDATE/JOIN/GROUP BY`；
- B-Tree 索引、组合索引最左前缀；
- `EXPLAIN`、N+1、游标分页；
- 多租户查询为什么必须包含 `tenant_id`。

验收：完成 SQL 练习，并用 `EXPLAIN` 比较有索引和无索引查询。

## 第 6 周：事务、并发更新与幂等

- ACID 与常见隔离级别；
- 丢失更新、悲观锁、乐观锁；
- 幂等键和唯一约束；
- Webhook 的验签、事件去重、顺序和重放；
- 进程宕机造成的失败窗口。

验收：针对重复回调、事务提交后宕机、响应丢失三种情况，写出状态变化和恢复方法。

## 第 7 周：Redis

- Redis 适合和不适合保存什么；
- Cache Aside、TTL、缓存穿透/击穿/雪崩；
- 限流、短期幂等和分布式锁的边界；
- 为什么不能把积分、工单状态只放在 Redis。

验收：运行缓存实验，证明缓存删除后仍能从事实源恢复。

## 第 8 周：异步、并发、超时与取消

- Python 事件循环和协程；
- Go goroutine、channel、WaitGroup；
- I/O 并发不等于 CPU 并行；
- deadline、超时传播、有限并发；
- 重试必须考虑幂等、退避和抖动。

验收：实现三个并发下游调用，其中一个超时不会无限阻塞整体请求。

## 第 9 周：Outbox、Redis Streams 与任务恢复

- “写数据库 + 发消息”的双写问题；
- Transactional Outbox；
- Consumer Group、Pending、ACK、claim；
- 至少一次投递与消费者幂等；
- retry、DLQ、租约与 fencing token。

验收：手工推演消费者处理成功前宕机、处理成功后 ACK 前宕机两种情况。

## 第 10 周：认证、安全与权限

- 密码哈希、JWT Access Token、Opaque Refresh Token；
- Authentication 与 Authorization；
- RBAC、资源 owner、多租户隔离；
- 注入、SSRF、日志泄密、密钥管理；
- 限流、审计和最小权限。

验收：写出三条越权测试，证明“前端隐藏按钮”不是权限控制。

## 第 11 周：测试与调试

- 单元、集成、契约、E2E 的边界；
- fake、mock、真实依赖分别证明什么；
- table-driven test 与 pytest fixture；
- 从复现、证据、假设到最小修复；
- AI 生成代码的审查清单。

验收：为一个真实缺陷先写失败测试，再修复并记录证据。

## 第 12 周：日志、指标与 Trace

- 结构化日志与 request/trace/event ID；
- RED：Rate、Errors、Duration；
- 队列积压、数据库连接和 AI 成本指标；
- readiness 与 liveness 的区别；
- SLO、告警和错误预算。

验收：给工单创建、Webhook 和异步消费设计指标与告警，不允许只写“打印日志”。

## 第 13 周：Docker、K8s 与 CI/CD

- Image、Container、Volume、Network；
- Docker Compose 本地依赖；
- K8s Deployment、Service、ConfigMap、Secret、Probe；
- migration Job、滚动发布、镜像 digest 和回滚；
- format、lint、test、build、scan、deploy、smoke。

验收：启动 PostgreSQL/Redis，解释数据卷和健康检查；能读懂一个 Deployment，但不要求独立维护生产集群。

## 第 14 周：gRPC、事件契约与服务边界

- REST、gRPC 和异步事件各自适用的场景；
- Protobuf 字段编号与兼容性；
- BFF 聚合与 owner service；
- 同步链路过长为什么脆弱；
- 契约版本升级。

验收：把一个跨服务需求拆成同步查询与异步事件，说明选择理由。

## 第 15 周：RAG/Agent 生产化

本周不重复讲 embedding 和基础检索，重点是：

- Provider/Tool Registry 与权限/成本控制；
- 结构化输入输出、超时、预算和降级；
- RAG 数据 owner、版本和权限过滤；
- 离线评测、Bad Case、在线指标；
- Prompt 注入、引用验证和敏感数据；
- 模型不可用时怎样明确失败。

验收：为熟悉的 RAG 增加请求预算、超时、来源、评测样本和稳定错误码。

## 第 16 周：综合项目与讲解

完成 [可靠工单 + Agent 任务后端](projects/reliable-support-agent/README.md)：

- Go Gateway/BFF；
- Python Agent Task Service；
- PostgreSQL 事实表和 Outbox；
- Redis 缓存与 Streams；
- Webhook 幂等；
- 测试、指标、Docker Compose 和故障演练。

最终验收不是代码行数，而是你能在不打开 AI 的情况下讲清楚：边界、事务、失败窗口、恢复、验证证据和仍未解决的限制。
