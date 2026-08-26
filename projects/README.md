# Projects：只在需要整合时使用

当前日常主线不从 `projects/` 开始，而从：

- [`../GO_BACKEND_TRACK.md`](../GO_BACKEND_TRACK.md)
- [`../exercises/go-ticket-api/`](../exercises/go-ticket-api/)

开始。

`projects/` 的作用是：

> 当多个后端概念已经分别理解以后，再把它们放进同一个系统，观察事务、身份、异步和部署之间的交互。

---

# 当前主参考项目已经移到 Go Ticket API

当前真正用于每天跟写和学习的是：

- [`../exercises/go-ticket-api/README.md`](../exercises/go-ticket-api/README.md)

它采用完整参考实现驱动的方式：

```text
对话讲解
→ 完整 Go 参考
→ 跟写必要代码
→ 独立小改
→ 故障实验
→ Review
```

不要求先从空白目录设计整个工程。

---

# `reliable-support-agent` 的新定位

原有：

- [`reliable-support-agent/`](reliable-support-agent/)

保留为**可选的后端与 Agent 集成参考**，不再是当前主学习项目。

原因：学习者已有单独的 Agent 学习仓库。本仓库主要补 Go 和传统后端能力，不重复学习 Agent 框架、Prompt、RAG 或 Eval。

这个项目只在需要验证下面的连接时使用：

```text
Agent Task
→ 持久状态 / Worker / Retry

Tool
→ Authentication / Authorization / Idempotency / Audit

RAG
→ tenant / ACL filtering / source lifecycle

Model Provider
→ timeout / budget / observability
```

如果当前只在学习 Router、Middleware、PostgreSQL 或事务，不需要打开 Agent 项目。

---

# 什么时候进入 Project

适合进入整合项目的信号：

```text
已经能单独解释一个概念
↓
想看它和其他边界怎样交互
```

例如：

```text
已经懂 transaction
→ 放进 create / close 流程

已经懂 idempotency
→ 模拟 COMMIT 后 response 前失败

已经懂 Worker
→ 模拟业务 COMMIT 后 ACK 前崩溃
```

不适合的理由：

```text
企业项目一般都有
想让架构图看起来高级
简历上想多写技术名
```

---

# 项目纪律

每加入一个组件都回答：

```text
前一版哪里不够？
这个组件解决什么？
它新增什么失败？
我怎么证明？
有没有更简单方案？
```

如果这些问题答不出来，就先回到 Go 主线和当前章节。

---

# AI 在 Project 中的角色

AI 可以提供：

- 完整参考实现；
- 设计和调用链解释；
- 失败测试；
- Code Review；
- 方案比较；
- 故障推演。

但项目完成的证据不是“AI 生成了全部代码”，而是学习者能够：

```text
解释请求链
指出事实 owner
说明 transaction 边界
处理重复与并发
定位失败
读懂测试与观测证据
```

---

当前结论：

> **日常学习跟随 Go Ticket API；`projects/` 只用于后续整合，Agent 项目是可选桥接，不再占据后端主线。**
