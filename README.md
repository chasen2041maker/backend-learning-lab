# Go 后端工程学习仓库

这是一个用于长期学习 **Go 后端工程** 的公开仓库。

主要学习方式不是独自按章节看书，也不是面对空白目录手搓所有样板代码，而是：

```text
和 AI 对话把问题与调用链讲通
↓
查看完整、正确、可运行的 Go 参考实现
↓
只跟写当前必要代码
↓
运行测试 / curl / 故障实验
↓
独立完成一个小变化
↓
AI Review
↓
把高价值理解和进度沉淀回 GitHub
```

目标是建立对后端和 AI 生成代码的控制力：

```text
看得懂
讲得清
改得对
测得出
出错能定位
知道什么时候不要增加复杂度
```

---

# 日常学习入口

按下面顺序使用：

1. **[`progress/current-focus.md`](progress/current-focus.md)**：当前真正学到哪里、下一次从哪里继续；
2. **[`GO_BACKEND_TRACK.md`](GO_BACKEND_TRACK.md)**：完整十二章 Go 后端主线；
3. **[`exercises/go-ticket-api/`](exercises/go-ticket-api/)**：主参考项目；
4. 当前章节对应的 walkthrough 和 practice。

当前主项目的三个入口：

- [`STUDY_ORDER.md`](exercises/go-ticket-api/STUDY_ORDER.md)：章节顺序与状态；
- [`CODE_MAP.md`](exercises/go-ticket-api/CODE_MAP.md)：文件与调用链地图；
- `walkthrough/`：带详细解释的参考代码；
- `practice/`：只要求独立完成的小变化与故障实验。

---

# 新 AI / 新电脑怎么接棒

新的 ChatGPT / Codex / AI 会话先读：

```text
1. LEARNER_PROFILE.md
2. progress/current-focus.md
3. GO_BACKEND_TRACK.md
4. 当前 walkthrough / code
```

不需要每次都先读完整 `GROWTH_PATH.md` 和 `LEARNING_ROADMAP.md`；它们只在长期规划、阶段复盘或技术选型时使用。

最新对话中的真实理解程度永远优先于可能陈旧的进度文件。

---

# 当前学习者定位

公开、长期有效的技术上下文：

```text
已在 Agent 工程岗位工作约 4 个月
日常使用 Codex / AI Coding 参与真实项目
Python 和 Agent/RAG 应用经验相对更好
Go 和传统后端基础仍然薄弱
```

因此本仓库不把学习者当作完全没有开发经验的新手，也不会强迫从空白开始重复大量样板代码。

默认模式：

```text
完整参考实现
+ 对话讲解
+ 跟写必要部分
+ 独立小改
+ 测试和故障
```

详细规则见 [`LEARNER_PROFILE.md`](LEARNER_PROFILE.md)。

---

# 仓库范围

本仓库主线负责：

```text
Go / net/http
HTTP / API Contract
Router / Middleware / Handler
Service / Repository
PostgreSQL / SQL
Authentication / Authorization
Transaction / Idempotency
Concurrency / Timeout / Cancel
Redis 的角色边界
Async / Outbox / Worker
Testing / Debugging / Observability
Docker / CI / Deployment
系统设计与复杂度控制
```

Agent / RAG / Prompt / Eval / Multi-Agent 有单独的学习仓库。本仓库只保留必要的后端连接，例如：

```text
Agent Task 仍需要持久状态
Tool 仍需要 Authorization / Idempotency / Audit
RAG 仍需要 tenant / ACL filtering
模型调用仍需要 timeout / budget / observability
```

原有 Agent 综合材料保留为可选参考，不再是当前主线。

---

# 主参考项目

## Go Ticket API

路径：

- [`exercises/go-ticket-api/`](exercises/go-ticket-api/)

它是一套完整可运行的 Go `net/http` 模块化单体基线，包含：

```text
http.Server
ServeMux / Router
Middleware
Authentication / Principal
Handler
Service
Repository
Memory storage
context.Context
mutex
状态机 / 版本冲突
稳定错误映射
handler / service tests
```

运行：

```powershell
cd exercises\go-ticket-api
go test ./...
go run ./cmd/server
```

服务默认监听：

```text
http://127.0.0.1:8080
```

当前项目是**参考教材项目**，不是要求一次从空白重写的挑战。详细注释放在 walkthrough，运行代码保持清楚、可测试。

---

# 十二章主线概览

```text
01 HTTP Server / Handler
02 Router / ServeMux
03 Middleware
04 Handler -> Service -> Repository
05 Error / Config / Logging / Testing
06 context.Context / Deadline / Cancel
07 PostgreSQL
08 Authentication / Authorization
09 Transaction / Idempotency
10 Concurrency / Redis
11 Async / Outbox / Worker
12 Observability / Docker / CI / Deployment
```

每章默认：

```text
对话讲解
→ 完整参考
→ 跟写必要代码
→ 运行
→ 独立小改
→ 故障实验
→ Review
```

完整目录见 [`GO_BACKEND_TRACK.md`](GO_BACKEND_TRACK.md)。

---

# 其他目录

```text
backend-learning-lab/
├─ GO_BACKEND_TRACK.md             # 当前唯一日常主线
├─ LEARNER_PROFILE.md              # 长期教学契约
├─ GROWTH_PATH.md                  # 长期能力成熟度地图
├─ LEARNING_ROADMAP.md             # 知识依赖地图
├─ lessons/                        # 通用、成熟的系统教程
├─ notes/                          # 术语、速查、学习轨迹
├─ exercises/
│  └─ go-ticket-api/               # 当前主参考项目
├─ contracts/                      # HTTP / Event 契约
├─ projects/                       # 可选整合项目
├─ progress/
│  └─ current-focus.md             # 精确接棒点
└─ scripts/                        # 自动校验
```

---

# 如何判断掌握

```text
L1 见过：知道名词和用途
L2 能解释：能画调用链、指出失败点
L3 能控制：能修改、测试、排错
L4 能权衡：知道什么时候不用、替代方案和成本
```

参考实现驱动并不降低标准。达到 L3 至少需要：

```text
读懂完整代码
+ 解释真实调用链
+ 独立完成一个变化
+ 写/改测试
+ 定位一个故障
```

不要求脱离所有参考从空白默写整个工程。

---

# 仓库更新约定

对话中说：

```text
更新仓库
```

表示：

```text
检查真正新增的长期知识或学习方式变化
→ 读取已有内容避免重复
→ 更新最合适的 track / profile / current-focus / walkthrough / journal
→ 原子提交到远端
→ 验证 branch / compare / CI
```

不是保存聊天全文。

---

# 公开仓库安全边界

永远不要提交：

- 公司源代码或内部架构；
- 内部域名、IP、日志、Prompt；
- 客户或用户数据；
- 密码、Token、API Key、Secret；
- 无法公开的业务材料。

只使用虚构业务和本地生成数据。

---

这个仓库最终要证明的不是“抄过多少代码”，而是：

> **即使大量使用 Codex，仍然能够对一次请求、一个业务事实、一次事务、一个并发冲突和一个故障恢复承担工程责任。**
