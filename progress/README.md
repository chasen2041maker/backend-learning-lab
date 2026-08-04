# 学习进度与独立能力验收

只有在“不看答案、能够解释并运行验证”后才能打勾。

## 请求、语言和分层

- [ ] 我能画出一次请求的完整链路和三个失败点。
- [ ] 我能在 Python 和 Go 中独立定义、验证 Ticket。
- [ ] 我能解释 Handler、Service、Repository 和 Domain。
- [ ] 我能独立新增字段并修复两套测试。
- [ ] 我能说明 deadline、timeout 和 cancel 的区别。

## API 与数据

- [ ] 我能先改契约，再改实现和测试。
- [ ] 我能写参数化 SQL、JOIN、聚合和游标分页。
- [ ] 我能用 EXPLAIN 说明查询是否使用索引。
- [ ] 我能解释事务能保护和不能保护什么。
- [ ] 我能演示一次乐观版本冲突。
- [ ] 我能证明所有查询执行 tenant/owner 过滤。

## Redis 与异步可靠性

- [ ] 我能解释 Cache Aside、TTL 和三类缓存风险。
- [ ] Redis 清空后，系统仍能从事实源恢复。
- [ ] 我能解释 Outbox 解决的双写问题。
- [ ] 我能解释 Streams、Group、Pending、ACK 和 Claim。
- [ ] 我能推演业务提交后、ACK 前宕机。
- [ ] 我能解释 lease 和 fencing token。

## 安全、质量与运行

- [ ] 我能区分认证、授权、owner 和 tenant。
- [ ] 我写过未登录、越权和跨租户测试。
- [ ] 我能从完整错误和关联 ID 找到第一个错误状态。
- [ ] 我能区分单元、集成、契约、E2E 和故障测试。
- [ ] 我能设计 HTTP RED、队列积压和任务指标。
- [ ] 我能解释 readiness 与 liveness。
- [ ] 我能运行 Compose 并解释 Volume、Network 和健康检查。
- [ ] 我能读懂基本 Deployment、Service、Secret 和 migration Job。

## Agent/RAG 生产化

- [ ] 检索在进入模型前执行权限过滤。
- [ ] Provider/Tool 有 schema、health、权限、成本和超时边界。
- [ ] 我有固定评测集和 Bad Case 根因标签。
- [ ] 我能解释模型、工具或数据不可用时的降级。
- [ ] 我能说明 Token、并发、deadline 和成本预算。

## 每日记录

```text
日期：
今天的可运行目标：
我先独立写了什么：
AI 只帮助了什么：
执行过的命令：
制造的失败：
根因与证据：
我现在能关闭 AI 解释什么：
明天从空白重写什么：
```
