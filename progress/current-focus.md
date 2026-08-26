# 当前学习接棒点

最后更新：2026-08-26

这份文件只回答：

> **下一次新的 ChatGPT / Codex 会话应该从哪里继续，以及当前采用什么学习方式？**

长期能力地图见 [`../GO_BACKEND_TRACK.md`](../GO_BACKEND_TRACK.md) 和 [`../GROWTH_PATH.md`](../GROWTH_PATH.md)。

---

# 当前技术学习定位

公开、长期有效的技术上下文：

```text
Agent 工程岗位约 4 个月
日常使用 Codex / AI Coding 参与真实项目
Python 和 Agent/RAG 应用经验相对更好
Go 与传统后端工程基础仍然薄弱
```

当前后端主线大致处于：

```text
GROWTH_PATH S0
→ 正在进入 S1 API 初学者
```

这只是后端基础切入点，不是对整体工作能力或职位的评价。

---

# 已确认的学习方式变化

从 2026-08-26 起，默认不再要求学习者从空白目录手搓整套项目。

采用：

```text
对话讲清问题和调用链
↓
完整、正确、可运行的参考实现
↓
跟写当前必要的 30～120 行代码
↓
运行测试 / curl / 故障实验
↓
独立完成一个小变化
↓
AI Review
```

学习者主要通过对话学习；代码用于建立控制力，不用于证明能否背着默写样板。

完整方法见：

- [`../LEARNER_PROFILE.md`](../LEARNER_PROFILE.md)
- [`../GO_BACKEND_TRACK.md`](../GO_BACKEND_TRACK.md)

---

# 已建立第一轮心智模型

以下内容已经能在提示较少时说出正确方向，但还需要在真实 Go 代码和测试中巩固。

## HTTP Request

已能区分：

```text
Method
Path
Route Pattern
Path Parameter
HTTP version
Host
Authorization Header
Accept
Content-Type
```

关键关系：

```text
Method + Route Pattern
→ 选择 Handler

Path Parameter
→ 决定当前 Handler 处理哪个资源
```

```text
Path 不存在
→ 404

Path 存在但 Method 不允许
→ 405
```

## Authentication / Authorization

已建立：

```text
Credential
→ Authentication
→ Principal
→ Authorization
```

```text
Authentication
= 你是谁

Authorization
= 你能做什么
```

以及：

```text
Authorization Header
= 携带 Credential
≠ 已经授权成功
```

## 网络到 Go

已建立第一轮关系：

```text
Client
→ Domain / DNS
→ IP + Port
→ listening socket
→ TCP connection
→ TLS
→ OS / Socket
→ Go process
→ net/http
→ *http.Request
```

当前深度已经足够继续后端主线，不需要继续深入 TCP 拥塞控制、TLS 密码套件或 Nginx worker 模型。

## Go `net/http`

已能解释：

```text
http.ListenAndServe
≠ 直接调用 Handler
```

它概念上包含监听、接受连接、解析 HTTP、构造 Request、调度 Handler 和写回 Response。

已理解：

```go
type Handler interface {
    ServeHTTP(http.ResponseWriter, *http.Request)
}
```

以及：

> `HandlerFunc` 拥有 `ServeHTTP` 方法，因此可以把普通 `func(w, r)` 适配成 `http.Handler`。

相关学习日志：

- [`../notes/learning-journal/2026-08-26-http-network-go-handler.md`](../notes/learning-journal/2026-08-26-http-network-go-handler.md)

---

# 当前精确章节

```text
GO_BACKEND_TRACK
第 3 章：Middleware
```

主项目：

- [`../exercises/go-ticket-api/`](../exercises/go-ticket-api/)

当前 walkthrough：

- [`../exercises/go-ticket-api/walkthrough/03-middleware.md`](../exercises/go-ticket-api/walkthrough/03-middleware.md)

当前 practice：

- [`../exercises/go-ticket-api/practice/03-middleware.md`](../exercises/go-ticket-api/practice/03-middleware.md)

---

# 下一次对话直接从这里开始

不要重新从 DNS、TCP、JWT 或 HandlerFunc 开始长篇复习，除非用户主动表示忘记。

先用当前真实代码讲清：

```go
func RequestContext(next http.Handler) http.Handler
func Authenticate(next http.Handler) http.Handler
```

顺序：

## 1. Middleware 的形状

```text
输入：一个 http.Handler
输出：一个新的 http.Handler
```

为什么它可以包装下一个 Handler。

## 2. `next.ServeHTTP(w, r)`

解释：

```text
继续把同一个 Request / ResponseWriter
交给链条中的下一层
```

不调用它会怎样；调用两次又会怎样。

## 3. Onion / Wrapper 顺序

使用最小例子说明：

```text
Outer before
→ Inner before
→ Handler
→ Inner after
→ Outer after
```

## 4. 读取当前项目的真实组合

当前 API 请求大致经过：

```text
RequestContext
→ root ServeMux
→ Authenticate
→ api ServeMux
→ endpoint Handler
```

`/health` 不经过 Authenticate。

## 5. 参考代码跟写

学习者按 walkthrough 跟写/阅读一个最小 AccessLog Middleware。

## 6. 独立小变化

至少完成一个：

```text
给 AccessLog 增加 request_id
或
补一个证明 middleware before/after 顺序的 test
```

## 7. 故障实验

临时注释掉：

```go
next.ServeHTTP(w, r)
```

运行测试，观察后面的 Router / Handler 为什么完全不执行。实验后恢复代码。

---

# 当前能力证据判断

```text
HTTP / 网络心智模型：L2 初步
http.Handler / HandlerFunc：L2 初步
Middleware：L1，正在进入 L2/L3
Go 独立实现能力：尚缺足够代码证据
```

不要因为对话中已经听懂，就标记 Middleware 为 L3。

达到 Middleware 当前小节完成，至少需要：

```text
能画 wrapper/onion 调用顺序
+ 能解释 next.ServeHTTP
+ 跑过现有测试
+ 完成一个独立小变化
+ 观察一次 chain 被截断的失败
```

---

# Middleware 之后

继续：

```text
第 4 章
Handler
→ Service
→ Repository
→ Memory / Database
```

重点不要求从空白重写整个项目，而是顺着现有 create/get 流程：

```text
HTTP JSON
→ Handler input
→ Service business rule
→ Repository persistence
→ response/error mapping
```

然后再进入：

```text
Error / Config / Testing
→ context.Context
→ PostgreSQL
```

---

# 新会话接棒规则

新的 AI：

1. 读 [`../LEARNER_PROFILE.md`](../LEARNER_PROFILE.md)；
2. 读本文件；
3. 读 [`../GO_BACKEND_TRACK.md`](../GO_BACKEND_TRACK.md) 当前章节；
4. 打开 Middleware walkthrough 和真实代码；
5. 对话优先，代码跟写按需要；
6. 不强迫从空白实现；
7. 每章仍要求一个独立变化和故障证据；
8. 最新用户消息优先于本文件。

当前一句话接棒：

> **从 Go Middleware 的 `func(next http.Handler) http.Handler`、`next.ServeHTTP` 和 onion 调用链继续；用现有 RequestContext / Authenticate 作为完整参考，学习者只跟写必要代码，再完成一个独立小改与 chain 截断故障实验。**
