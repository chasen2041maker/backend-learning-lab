# 20 周 Python 主线 + Go 复现路线

每天建议 60～90 分钟；“周”只是容量上限，不是截止日期。Python 先学并完成验收，Go 永远落后 1～2 个阶段，用来复现已经理解的后端概念，而不是同时学习两套新知识。若一周验收没通过，就顺延，不把欠账带到下一阶段。

当前求职目标所需优先级：后端可靠性、SQL、Redis、并发、测试、容器、系统设计、Agent 工程化高于重新系统学习 GAN、强化学习或训练模型。后者不是永远不学，而是等主线项目能独立讲清后再按岗位补。

## 第 0 周：环境、Git 与 AI 使用边界

- 进程、端口、环境变量、依赖、工作目录；
- Git commit/diff/branch 与公开仓库脱敏；
- AI 可以解释和审查，但每段合入代码必须能自己运行、测试、复述。

验收：关闭 AI，分别运行 Python、Go 测试，并根据失败信息定位文件。

## 第 1 周：HTTP 请求生命周期（Python）

- DNS/TCP/HTTP、反向代理、Handler、Service、数据库；
- Method、Path、Header、Body、状态码、request ID；
- 超时可能发生在哪一层。

验收：画出 `POST /tickets` 完整路径并标出三个失败点。

## 第 2 周：Python 后端基础

- 类型提示、dataclass/Pydantic、异常、Protocol；
- `async/await`、上下文管理与资源关闭；
- Handler/Service/Repository 的职责。

验收：不用 AI 新增 `priority` 字段并修复测试。

## 第 3 周：先测试再扩展 Python API

- 单元测试、Handler 测试、fake 与真实依赖的边界；
- 输入验证、稳定错误码、未知异常 Envelope；
- 状态机和乐观版本的第一版。

验收：先写失败测试，再完成关闭工单与冲突处理。

## 第 4 周：契约、身份与租户边界

- OpenAPI、兼容变更、严格 JSON、Unicode 与 UUID；
- Authentication 产生可信 Principal，Authorization 检查权限/owner/tenant；
- 客户端不能自报租户；共享契约测试防止多实现漂移。

验收：运行 `contracts/http-cases.json`，解释三条越权测试。

## 第 5 周：Docker 与本地依赖

- Image、Container、Volume、Network、端口绑定；
- Compose 启动 PostgreSQL/Redis，健康检查与数据卷；
- Tag、digest、环境变量与本地弱口令边界。

验收：启动/停止依赖，说明删除容器和删除 Volume 的区别。

## 第 6 周：SQL 与 PostgreSQL 基础

- DDL/DML、主外键、唯一/检查约束；
- JOIN/GROUP BY、B-Tree/组合索引、`EXPLAIN`、N+1；
- 每条租户查询都包含 `tenant_id`，游标分页使用 `(created_at,id)`。

验收：完成 SQL challenge，并比较有无索引执行计划。

## 第 7 周：Python 接入 PostgreSQL

- migration 前滚/回滚策略，禁止应用启动时并发乱跑 DDL；
- 连接池大小、获取连接超时、statement timeout、取消与资源预算；
- deadlock 识别/有限重试、备份恢复演练；
- Repository 集成测试与事务边界。

验收：写一个 migration 和集成测试，模拟超时并确认连接被释放。

## 第 8 周：Go 语言后端基础（复现第 1～3 周）

- package/module、struct、slice/map、pointer、method、interface；
- `(value, error)`、`errors.Is`、`defer`、`context.Context`；
- goroutine/channel 只学能读懂的最小集合。

验收：不用框架写一个有测试的 Handler → Service → Repository。

## 第 9 周：Go API 与共享契约（复现第 4 周）

- `net/http` 路由、中间件、严格 JSON、graceful shutdown；
- 可信 Principal 和 tenant-scoped Repository；
- 与 Python 读取同一份契约用例。

验收：Python/Go 契约测试同时通过，能解释行为差异如何被发现。

## 第 10 周：事务、并发更新与幂等

- ACID、隔离级别、丢失更新、乐观/悲观锁；
- 幂等键 + 唯一约束 + 请求哈希；
- 提交后响应丢失、并发重复请求和 deadlock 的恢复。

验收：为三种失败窗口写状态表和测试证据。

## 第 11 周：Redis 的运行时边界

- Cache Aside、TTL、穿透/击穿/雪崩；
- 连接池、command timeout、最大内存、淘汰策略、持久化和重启；
- 限流/短期幂等/锁的边界；事实状态不能只放 Redis。

验收：缓存删除后从事实库恢复，并说明 Redis 不可用时降级还是失败。

## 第 12 周：异步并发、超时与取消

- Python event loop 与 Go goroutine 的 I/O 并发；
- deadline 传播、有限并发、背压；
- 重试只针对可重试错误，并带退避、抖动、次数和总预算。

验收：运行 `reliability-labs/concurrency_timeout.py` 测试，证明慢依赖不会无限拖住整体。

## 第 13 周：Webhook、认证与安全

- 原始字节 HMAC、时间窗、event ID 去重与乱序；
- 密码哈希/JWT/opaque refresh token 的职责（不手写密码学）；
- RBAC/owner/tenant、注入、SSRF、日志泄密、最小权限。

验收：修改一个 JSON 空白但不改语义，证明“解析后再签名”为何会失败。

## 第 14 周：Outbox、Streams 与恢复

- 双写问题与 Transactional Outbox；
- claim/lease/fencing、有限重试、DLQ；
- Consumer Group、Pending、ACK、`XAUTOCLAIM`、消费者幂等。

验收：完成 Redis `consume-crash → pending → reclaim`，并运行 Outbox fencing 测试。

## 第 15 周：测试、调试与 CI

- unit/integration/contract/E2E 各证明什么；
- 从复现、证据、假设、最小修复到回归测试；
- format/lint/race/SQL/Compose/link/secret scan；
- AI 代码送审必须附测试证据与未解决限制。

验收：为真实缺陷先写失败测试，再修复并记录 debug log。

## 第 16 周：日志、指标、Trace 与资源预算

- 结构化日志与 request/trace/event ID；
- RED、队列积压、连接池、Agent 延迟/Token/费用；
- CPU/内存/连接/goroutine/任务并发预算；
- liveness/readiness、SLO、告警和错误预算。

验收：暴露指标并设计三条有阈值、有持续时间、有行动的告警。

## 第 17 周：部署与 K8s 阅读能力

- 多阶段构建、非 root、只读文件系统、镜像 digest；
- Deployment/Service/ConfigMap/Secret/Probe；
- migration Job、滚动发布、回滚与 smoke test。

验收：通过 K8s dry-run，解释 requests/limits 和两个 Probe；不要求维护生产集群。

## 第 18 周：服务边界与通信

- REST/gRPC/事件的取舍；Protobuf 字段兼容；
- BFF 聚合与 owner service，不跨服务写表；
- 同步链路过长、级联超时与容量估算。

验收：把一个跨服务需求拆成同步查询和异步事件并说明理由。

## 第 19 周：RAG/Agent 生产化

- Provider/Tool Registry、结构化输入输出、deadline、预算、降级；
- tenant 权限过滤、来源、离线评测与 Bad Case；
- Prompt 注入与敏感数据；模型输出永远不是权限决定；
- 有副作用 Tool 必须 allowlist、授权、人工确认、幂等、审计与补偿。

验收：运行 Fake RAG 与 Tool Authorization 测试，证明跨租户来源和未确认写操作被拒绝。

## 第 20 周：分阶段综合项目与讲解

按 [项目阶段](projects/reliable-support-agent/phases.md) 一次只完成一个可运行切片，每个阶段打 Tag 后再进入下一阶段。最终关闭 AI 录制 10 分钟讲解：边界、事务、失败窗口、恢复、验证证据和仍未解决的限制。
