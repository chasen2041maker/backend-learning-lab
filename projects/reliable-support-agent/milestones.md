# 综合项目里程碑

## M0：设计先行

- 写用例、非目标和容量假设；
- 冻结第一版 HTTP/事件契约；
- 画正常链路和失败窗口；
- 建立 CI，但暂不接真实依赖。

## M1：内存版同步 API

- Python Ticket Service；
- Go Gateway；
- 统一错误和 request ID；
- Service/Handler 单元测试。

## M2：PostgreSQL

- migration；
- Repository 与事务；
- tenant isolation；
- 乐观锁、游标分页和索引；
- Repository 集成测试。

## M3：幂等 Webhook

- 原始字节 HMAC；
- 时间窗和 nonce；
- 事件唯一约束；
- 严格实体 version/sequence；
- 重复、乱序、宕机测试。

## M4：Outbox + Redis Streams

- Outbox publisher；
- Consumer group；
- consumer 幂等；
- retry/DLQ；
- Pending reclaim 与积压指标。

## M5：Agent Task 与 RAG

- 任务状态机；
- claim/lease/fencing；
- Provider Registry；
- tenant 权限过滤；
- deadline、预算和取消；
- SSE 进度与断线恢复；
- 固定评测样本。

## M6：安全、观测和故障演练

- 测试身份、RBAC 和 owner；
- 结构化日志、指标和 Probe；
- Docker Compose；
- 敏感信息检查；
- 至少六个故障实验及恢复证据。

## M7：独立讲解与送审

- 运行所有检查；
- 完成验收清单；
- 生成一页架构说明；
- 关闭 AI 录制 10 分钟讲解；
- 使用根目录送审模板让 GPT 审查整个仓库。
