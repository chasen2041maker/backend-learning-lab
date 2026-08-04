# 综合项目：可靠工单 + Agent 任务后端

## 项目目标

为虚构 SaaS 产品构建一套最小但可靠的后端：用户创建工单，外部客服系统通过 Webhook 回传状态；用户可以发起 RAG/Agent 辅助分析任务，并通过 SSE 查看进度。

项目用于证明你能把已有的 Agent 经验与后端基本功连接起来。它不复制任何公司代码、接口或数据。

## 必须实现

### Go Gateway/BFF

- 版本化 REST API；
- 验证测试 Token 并注入可信用户/租户；
- 转发 Ticket 与 Agent Task 请求；
- 透传 request/trace ID；
- 下游 timeout、稳定错误映射和有限降级；
- 不直接写 owner service 的表。

### Python Ticket/Agent Service

- FastAPI Handler → Service → Repository；
- PostgreSQL 工单、消息、任务、幂等、Outbox；
- 工单状态机与乐观版本；
- Webhook 原始字节 HMAC、时间窗、nonce/event 去重；
- RAG Provider 接口、权限过滤、超时和来源；
- Agent Task 状态、取消、失败和 SSE 事件；
- 不可用 Provider 明确失败，不由模型补事实。

### 异步链路

- PostgreSQL Transactional Outbox；
- Publisher 写 Redis Streams；
- Consumer Group、ACK、Pending 接管；
- `event_id` 消费幂等；
- 有限重试、指数退避和 DLQ；
- 长任务租约与 fencing token。

### 工程质量

- Python pytest、Go test；
- PostgreSQL/Redis 集成测试；
- HTTP/事件契约测试；
- 结构化日志、HTTP RED、Outbox/Stream/Agent 指标；
- Docker Compose 本地运行；
- CI 执行 format、lint、test 和敏感信息检查；
- 故障演练记录。

## 明确不做

- 真实用户、支付或生产凭据；
- 复杂前端；
- 自建 Kubernetes 集群；
- 训练大模型；
- 为了展示而引入 Kafka、Elasticsearch或多个数据库；
- 公司代码和内部信息。

## 完成顺序

按照 [里程碑](milestones.md) 逐步实现。每个里程碑必须满足 [验收清单](acceptance.md)，不要一次让 AI 生成整个项目。
