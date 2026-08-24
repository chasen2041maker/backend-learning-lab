# Projects：把已经理解的知识放进同一个系统

`projects/` 不是用来一次生成“大而全企业项目”的地方。

它的作用是：

> **当某几个后端概念已经分别理解以后，把它们按最小增量整合到一个长期可演进的系统里。**

当前综合项目：

- [`reliable-support-agent/`](reliable-support-agent/)：可靠工单 + Agent 后端。

---

## 为什么只有一个主项目

学习后端不需要为每个技术建一个巨大项目。

真正有价值的是看到同一个系统怎么从：

```text
单服务 + 内存
↓
PostgreSQL
↓
Transaction / Auth / Idempotency
↓
Redis / Concurrency（确有需要时）
↓
Outbox / Worker
↓
Agent / RAG
↓
可选 Gateway / K8s
```

逐步演进。

这样每个新组件都有前一版本的真实痛点，而不是为了技术栈清单存在。

---

## 什么时候应该来做 Project

不是“Lesson 看完就必须做”。

更适合在你已经能单独解释某个概念以后：

```text
我已经懂 transaction
→ 把 transaction 放进真实 create/close 流程

我已经懂 idempotency
→ 模拟 COMMIT 后 response 前失败

我已经懂 Agent Tool 权限
→ 在真实 task/tool 流里验证
```

Project 的价值是整合和暴露交互问题。

---

## 当前项目入口

进入 [`reliable-support-agent/README.md`](reliable-support-agent/README.md) 后，按需要看：

- [`phases.md`](reliable-support-agent/phases.md)：系统为什么逐阶段增加复杂度；
- [`architecture.md`](reliable-support-agent/architecture.md)：每阶段架构和失败边界；
- [`acceptance.md`](reliable-support-agent/acceptance.md)：当前阶段究竟要证明什么；
- [`milestones.md`](reliable-support-agent/milestones.md)：能力证据，而不是功能完成率。

---

## 项目最重要的纪律

每加入一个组件，都回答：

```text
前一版具体哪里不够？
这个组件解决什么？
它新增什么失败？
我怎么证明？
有没有更简单方案？
```

如果只能回答：

```text
“企业项目一般都有”
```

就先不要加。

---

## AI 在 Project 里的角色

AI 可以：

- 解释设计；
- review；
- 帮你设计失败测试；
- 在明确要求时给 reference implementation；
- 帮你比较不同方案。

但不能把：

```text
AI 一次生成了 P0～P6
```

当成学习完成。

真正验收是你能自己解释请求链、事实 owner、transaction、重复、宕机恢复和测试证据。

---

## 项目做到哪算“完成”

不要求一定做到最后一个 Phase。

如果做到 P2，你已经能非常扎实地独立解释：

```text
HTTP
分层
PostgreSQL
Transaction
Authentication
Authorization
Idempotency
并发冲突
```

这比让 AI 帮你启动一个包含 Kafka/K8s/微服务但自己讲不清的 P6 更有价值。

项目的终点由能力决定，不由技术数量决定。
