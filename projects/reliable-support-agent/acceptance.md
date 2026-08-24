# 综合项目验收：每阶段只验当前承诺，不用终局清单压早期版本

旧式大清单容易出现一个问题：

```text
P0 还在学 Handler
却因为没有 Redis/K8s/Agent 看起来“项目未完成”
```

现在按阶段验收。

原则：

> **早期简单不是缺陷，只要它明确知道当前不解决什么。**

---

# 所有阶段都必须满足的基础线

- [ ] 仓库不包含真实公司代码、内部地址、客户数据、真实 Token/Secret。
- [ ] 当前阶段的 API/行为有明确契约。
- [ ] 当前阶段新增代码有对应测试或可重复验证步骤。
- [ ] 错误不会只返回“发生错误”，有可定位的 stable code / log evidence。
- [ ] 能说明当前 source of truth 在哪里。
- [ ] 能说明至少一个当前版本明确不解决的问题。
- [ ] 能关闭 AI 画出当前数据流。

---

# P0：内存 API

## 功能

- [ ] healthz 可用，非允许 Method 行为明确。
- [ ] create/get/list/close Ticket 可用。
- [ ] strict input / unknown field 行为与契约一致。
- [ ] request ID 在响应/日志中可关联。
- [ ] 非法状态转换有稳定错误。

## 分层

- [ ] Handler 处理 HTTP，不直接实现所有业务规则。
- [ ] Service 表达用例/状态规则。
- [ ] Repository 抽象内存数据访问。

## 证明

- [ ] unit/handler tests 通过。
- [ ] 能演示进程重启后数据消失，并解释这是 P0 的预期限制。

---

# P1：PostgreSQL

## Schema / SQL

- [ ] migration 能从空库执行。
- [ ] PK/UNIQUE/CHECK/FK 只在有业务不变量时使用并能解释理由。
- [ ] 所有用户输入通过参数化查询，不拼 SQL。
- [ ] tenant/owner 条件进入 Repository SQL。
- [ ] 列表排序稳定，cursor pagination 不重复/漏掉基本边界 case。

## Index / Performance

- [ ] 至少一个关键查询有 `EXPLAIN` 证据。
- [ ] 索引由真实查询模式推导，不是“重要字段全加”。

## Runtime

- [ ] connection pool 有上限。
- [ ] DB 获取/statement/request 不会无限等待。
- [ ] DB unavailable 返回明确失败，不悄悄改用内存事实。

## 证明

- [ ] PostgreSQL integration tests 通过。
- [ ] API 重启后事实仍存在。
- [ ] 非法 DB fact 被 constraint 拒绝。

---

# P2：Transaction / Auth / Idempotency

## Transaction / Concurrency

- [ ] 多行同一业务变化有明确 transaction boundary。
- [ ] optimistic version conflict 可稳定复现。
- [ ] rows affected=0 被当冲突处理，不当成功。
- [ ] 不在持锁 transaction 内做无界慢外部调用。

## Idempotency

- [ ] create 等关键副作用支持 persistent Idempotency Key。
- [ ] 相同 key + 相同 request 返回同一逻辑结果。
- [ ] 相同 key + 不同 request 被明确拒绝。
- [ ] 两个相同 key 的并发首次请求仍只产生一个业务结果。
- [ ] COMMIT 后 Response 前故障实验通过。

## Identity / Authorization

- [ ] Credential 只能通过服务端验证后生成 Principal。
- [ ] client Body `user_id/tenant_id/role` 不会成为可信身份。
- [ ] 未认证 case 通过。
- [ ] 无权限 case 通过。
- [ ] 跨租户 case 通过。

---

# P3：Concurrency / Redis（只验选择的 Track）

## 如果选择并发 Track

- [ ] 并发有明确上限。
- [ ] 下游有 deadline/timeout。
- [ ] cancellation 能向下游传播。
- [ ] race detector / concurrency test 有实际证据。
- [ ] retry 只针对明确可重试错误，带 backoff/jitter/总预算。
- [ ] 没有无限 goroutine/task/queue。

## 如果选择 Redis Cache

- [ ] PostgreSQL 仍是 source of truth。
- [ ] cache miss 可重建。
- [ ] TTL/invalidation policy 明确。
- [ ] Redis flush 后业务事实不丢。
- [ ] Redis unavailable 时的回源/失败策略不会无限打 DB。

## 如果选择 Session / Rate Limit

- [ ] 明确 Redis 数据丢失的业务后果。
- [ ] fail-open / fail-closed 是有意识的决定。
- [ ] 不把关键永久事实只放 Redis。

---

# P4：Webhook / Outbox / Worker

## Webhook

- [ ] 对原始 body bytes 验证 HMAC。
- [ ] timestamp/replay window 明确。
- [ ] provider event ID 有持久唯一约束。
- [ ] duplicate event 不重复应用。
- [ ] stale/out-of-order event 有 version/sequence policy。

## Outbox

- [ ] 业务变化与 outbox row 同一 DB transaction。
- [ ] Publisher crash 后未完成事件可重新发现。
- [ ] publish 成功但 mark published 前 crash 会重复，但不会让业务不一致。

## Consumer

- [ ] Consumer 业务更新和 processed-event 记录有原子边界。
- [ ] COMMIT 后 ACK 前 crash 可恢复。
- [ ] Pending/reclaim 可演示。
- [ ] poison message 不无限热循环。
- [ ] retry 有上限/退避。
- [ ] DLQ 有告警和重放说明。

## Observability

- [ ] backlog count / oldest age 可观察。
- [ ] Pending oldest age 可观察。
- [ ] retry / failure / DLQ 可观察。

---

# P5：Agent / RAG

## Task Lifecycle

- [ ] task 有持久状态：pending/running/terminal。
- [ ] worker ownership 有 lease/version/fencing 或等价保护。
- [ ] cancel 是明确业务动作，不等于 SSE disconnect。
- [ ] SSE 断线后可以 query 恢复 task state。

## RAG

- [ ] tenant/ACL filter 在模型看到内容前执行。
- [ ] chunk/index 保留足够 owner/version metadata。
- [ ] no relevant source 有明确 outcome。
- [ ] citation 来自真实 retrieval result，不由模型凭空生成 source ID。

## Model / Budget

- [ ] model call 有 deadline。
- [ ] max step/tool/token/result-size/cost 中至少定义适合系统的预算边界。
- [ ] provider 429/timeout/5xx 有稳定错误策略。
- [ ] fallback 不绕过权限和 Tool side-effect 语义。

## Tools

- [ ] Model Tool Call 只被当成不可信结构化请求。
- [ ] Tool schema 服务端再验证。
- [ ] Tool 做 permission + tenant/owner check。
- [ ] side-effect Tool 有 idempotency。
- [ ] 高风险 Tool 有 confirmation policy。
- [ ] Tool 执行有 audit evidence。

## Eval

- [ ] 有固定测试样本，而不是只手测几个 Prompt。
- [ ] Bad Case 能区分 retrieval/model/tool/permission/timeout 等根因。
- [ ] 至少观察 latency/token/tool failure/no-source 等 online signals。

---

# P6：可选 Gateway / Deployment

## 如果拆 Gateway / Service

- [ ] 有明确“为什么网络边界值得存在”的理由。
- [ ] 下游不信任公网客户端伪造的内部身份 Header。
- [ ] service-to-service 调用有身份/来源验证。
- [ ] deadline 可跨服务传播。
- [ ] error mapping 稳定。
- [ ] retry owner 明确，不形成多层放大。
- [ ] trace/request context 可跨服务关联。

## Docker / CI

- [ ] Image 可重复 build。
- [ ] runtime 尽量 non-root / least privilege。
- [ ] Secret 不 baked into Image。
- [ ] CI 实际运行 format/lint/test/contract 等当前可用检查。
- [ ] 发布使用可识别 artifact/tag/digest。

## Kubernetes（如果做）

- [ ] 能解释 Pod/Deployment/Service。
- [ ] resources 有理由，不是复制模板数字。
- [ ] readiness/liveness 语义正确。
- [ ] graceful shutdown 配合 rollout。
- [ ] migration 与新旧版本兼容性有说明。
- [ ] rollback 不被错误理解成“镜像切回去就一定行”。

---

# 最终口头验收

无论做到哪个 Phase，都应该能在 5～10 分钟内说明：

```text
当前目标和非目标
当前架构为什么这么简单/复杂
一次核心请求的数据流
source of truth
身份/tenant 边界
transaction/并发/idempotency
最大失败窗口
恢复方式
测试/观测证据
当前明确没有解决什么
下一组件只有在什么条件下才会加入
```

如果这些讲不清，先不要因为 checklist 勾得很多就进入下一阶段。
