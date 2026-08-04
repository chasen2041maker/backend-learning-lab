# 综合项目验收清单

## 功能

- [ ] 创建、查询、列表、关闭工单；
- [ ] 重复创建请求返回同一结果；
- [ ] Webhook 重复和乱序不会重复应用；
- [ ] Agent Task 支持成功、失败、取消和超时；
- [ ] SSE 断开后可以查询恢复终态。

## 数据与一致性

- [ ] 所有业务查询包含 tenant/owner 条件；
- [ ] 约束和索引与查询匹配；
- [ ] 状态变更与 Outbox 同事务；
- [ ] 并发更新使用乐观锁或明确锁策略；
- [ ] Redis 丢失不会丢业务事实；
- [ ] 消费者至少一次投递下仍幂等。

## 安全

- [ ] 不信任客户端 user_id；
- [ ] Webhook 按原始字节验签；
- [ ] Token/Secret/隐私不进入日志；
- [ ] RAG 检索执行租户权限过滤；
- [ ] 输入、响应大小、URL 和重定向有边界；
- [ ] 三类越权测试通过。

## 可靠性和观测

- [ ] 所有外部调用有 deadline；
- [ ] 重试有限、带退避且只用于可重试错误；
- [ ] 日志包含 request/trace/event ID；
- [ ] 有 HTTP RED、Outbox backlog、Pending age、Agent 成本指标；
- [ ] readiness 检查必要依赖；
- [ ] 故障演练能证明恢复而不是只证明报错。

## 代码与验证

- [ ] Python format/lint/test；
- [ ] Go fmt/vet/test；
- [ ] SQL migration 可从空库执行；
- [ ] 契约与实现同步；
- [ ] Docker Compose 可重复启动；
- [ ] 无公司信息、密钥、真实数据；
- [ ] 能独立讲清最大失败窗口和当前限制。
