# 学习者画像与教学契约

这份文件只保存会长期影响教学方式的**技术学习上下文**。它不是简历，也不记录公司机密、私人生活或真实业务数据。

新的 ChatGPT / Codex / AI 会话开始后，先读本文件，再读 [`progress/current-focus.md`](progress/current-focus.md) 和 [`GO_BACKEND_TRACK.md`](GO_BACKEND_TRACK.md)。

---

# 1. 当前技术背景

可以长期假设：

- 已在 Agent 工程岗位工作约 4 个月；
- 日常会使用 Codex / AI Coding 参与真实项目开发；
- Python 基础和 Agent/RAG 应用经验相对更好；
- Go 基础、传统后端工程、SQL、事务、并发、Redis、部署等仍然薄弱；
- 已见过 Go struct、interface、error、JSON、`net/http`、goroutine、channel 等，但“见过”不代表能够独立控制；
- 已系统讨论 Cookie、Session、Token、Bearer、JWT、Authentication / Authorization，但仍需要在真实代码链中反复连接。

因此，不要把学习者当作完全没有开发经验的学生，也不要因为他在工作中使用 Codex，就默认已经具备成熟后端判断。

---

# 2. 长期目标

目标不是脱离所有工具默写一个大项目，也不是只会让 AI 生成代码。

长期目标是获得成熟后端工程师常见的控制力：

```text
看到需求
↓
定位请求、身份、业务和数据边界
↓
从简单正确方案开始
↓
推演事务、并发、重复、超时和宕机
↓
用测试、日志、指标和故障实验验证
↓
读懂并约束 AI 生成代码
↓
能独立修改、排错和做技术取舍
```

“约 10 年开发成熟度”只是一组长期能力参照，不是时间承诺或职位标签。

---

# 3. 仓库分工

本仓库专门学习：

```text
Go 后端工程
HTTP / API
PostgreSQL
Authentication / Authorization
Transaction / Idempotency
Concurrency / Timeout / Cancel
Redis
Async / Outbox / Worker
Testing / Debugging / Observability
Docker / CI / Deployment
系统设计和复杂度控制
```

Agent / RAG / Prompt / Eval / Multi-Agent 由单独的 Agent 学习仓库承担。

这里可以使用 Agent Task、Tool 或 RAG 作为后端案例，但不重复系统学习 Agent 框架。

---

# 4. 主要学习方式：对话优先

主要通过和 AI 对话学习，而不是独自按章节阅读。

默认循环：

```text
提出问题 / 看真实代码
↓
AI 把调用链和心智模型讲通
↓
查看完整、正确、可运行的参考实现
↓
只跟写当前必要代码
↓
运行测试 / curl / 故障实验
↓
学习者独立完成一个小变化
↓
AI Review
↓
把高价值知识与进度沉淀回仓库
```

如果当天只想理解概念，可以先不写代码；但一个章节最终应至少完成一次小改动、测试或故障验证。

---

# 5. 代码教学方式：完整参考实现驱动

## 5.1 不默认要求从空白开始

当前默认不是：

```text
只给目标
→ 学习者面对空白目录构造整个项目
```

而是：

```text
先给最终正确结构和完整参考代码
→ 讲清调用链
→ 学习者跟写当前必要的 30～120 行
→ 运行
→ 再独立修改一个小点
```

原因：学习者已经在工作中使用 AI Coding，需要优先提升阅读、控制、验证和排错能力，而不是把大量时间消耗在重复样板代码上。

## 5.2 详细注释放在 walkthrough

工作代码保持接近真实工程风格；详细解释写在 walkthrough 中。

注释重点是：

```text
为什么存在
谁调用
输入来自哪里
职责是什么
不应该知道什么
输出交给谁
失败会怎样
```

不需要给每一行写“定义变量”式注释。

## 5.3 每章必须有一个独立小变化

虽然不要求从零重写整章，但要独立完成至少一个变化，例如：

- 补一个 405 测试；
- 给 Middleware 增加一个日志字段；
- 新增 `priority`；
- 补跨租户测试；
- 给 Slow Repository 加 deadline；
- 为重复请求增加幂等验证。

## 5.4 每章至少看一个失败

例如：

```text
不调用 next.ServeHTTP
→ 后续 Handler 不执行

Service 使用 context.Background()
→ 请求取消不能传播

COMMIT 后响应前失败
→ 重试可能重复创建
```

---

# 6. 新概念第一次出现时怎么讲

默认按下面顺序：

```text
1. 一句话定义
2. 为什么需要它
3. 上一层给它什么
4. 它负责什么
5. 它不负责什么
6. 它给下一层什么
7. 一个真实最小例子
8. 一个失败症状
9. 一个常见误区
10. 和已学知识连接
```

例如不要只说：

```text
Middleware 是中间件。
```

而要说明：

```text
Middleware 接收一个 http.Handler，返回一个新的 http.Handler；它可以在 next.ServeHTTP 前后执行公共逻辑，因此适合 Request ID、日志、认证等横切职责。
```

展开深度以能够解释后端现象和故障为准；不要为了完整继续深入 TCP 拥塞控制、TLS 密码套件或内核网络实现。

---

# 7. 讲 Go 代码的顺序

不要先逐行翻译语法。

默认顺序：

```text
谁调用这个函数
↓
输入从哪里来
↓
状态在哪里改变
↓
错误如何传播
↓
输出交给谁
↓
最后再讲关键 Go 语法
```

特别关注：

```text
http.Handler / HandlerFunc
Middleware chain
context.Context
interface
(value, error)
errors.Is
mutex / channel
tests
```

---

# 8. 掌握等级

```text
L0 未接触
L1 见过：知道名词和大概用途
L2 能解释：能画调用链并指出失败点
L3 能控制：能修改、测试、排错
L4 能权衡：知道什么时候不用、替代方案和成本
```

在这条参考实现驱动路线中，L3 不要求完全脱离参考从空白重写，而要求：

```text
能读完整代码
+ 能解释真实调用链
+ 能独立完成一个变化
+ 能写/改测试
+ 能定位一个故障
```

---

# 9. 新 AI 会话启动顺序

日常教学只需读：

```text
1. LEARNER_PROFILE.md
2. progress/current-focus.md
3. GO_BACKEND_TRACK.md
4. 当前章节 walkthrough / code
```

只有做长期阶段规划时再读：

```text
GROWTH_PATH.md
LEARNING_ROADMAP.md
```

新会话必须：

- 从 `current-focus` 继续，不机械从头复习；
- 用户已经能准确复述的内容快速通过；
- 用户说模糊时立即降速；
- 最新用户表现优先于仓库中可能陈旧的 checkpoint；
- 用户说“更新仓库”时，再更新有长期价值的内容和接棒点。

---

# 10. 不应该做的事情

不要：

- 强迫学习者为证明认真而从空白重写所有样板代码；
- 一次让 Codex 生成整个终局项目后只看测试绿；
- 同时维护完整 Python 和 Go 两套主业务实现；
- 把 Agent 课程重新塞进本仓库主线；
- 因为出现“高并发”三个字就加 Redis/Kafka/K8s；
- 只解释语法，不解释调用链和失败边界；
- 把前端按钮、Prompt 或客户端自报 tenant 当安全边界；
- 因为 CI 通过就宣称代码达到生产级；
- 为了仓库变大而重复创建文档。

---

当前主线和十二章目录见 [`GO_BACKEND_TRACK.md`](GO_BACKEND_TRACK.md)，精确接棒位置见 [`progress/current-focus.md`](progress/current-focus.md)。
