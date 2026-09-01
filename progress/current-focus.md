# 当前学习接棒点

最后更新：2026-09-01

这份文件只回答：

> **下一次新的 ChatGPT / Codex 会话应该从哪里继续，以及当前采用什么学习方式？**

长期能力地图见 [`../GO_BACKEND_TRACK.md`](../GO_BACKEND_TRACK.md) 和 [`../GROWTH_PATH.md`](../GROWTH_PATH.md)。

最近两次详细学习记录：

- [`2026-08-31.md`](2026-08-31.md)：Repository / MemoryRepository / Version / RWMutex；
- [`2026-09-01.md`](2026-09-01.md)：`context.Context` 请求生命周期传播、`Err()` / `Done()`。

---

# 当前技术学习定位

```text
Python / Agent 应用经验相对更强
Go 语法与传统后端工程仍是主要短板
当前目标不是从空白默写项目
而是通过对话 + 完整参考代码建立对后端代码的控制力
```

当前后端主线仍处于基础 API 工程阶段。第 4 章 Handler → Service → Repository 已建立较完整的 L2 对话心智模型，但尚未完成独立小改、测试和故障实验，因此不要标记 L3。

当前正在沿第 4 章真实调用链，自然进入第 6 章的 `context.Context` 概念。

---

# 当前教学方式：必须保持

用户主要通过对话学习。讲 Go 后端时继续保持：

```text
1. 先讲这段代码解决什么真实后端问题
2. 顺请求 / 数据 / 状态变化讲谁调用谁
3. 说明失败怎么传播
4. Go 语法挡住理解时，再局部用 Python 类比拆语法
5. 回到真实 Go 代码
```

不要变成脱离项目的 Go 语法课，也不要突然跳到数据库、K8s、Redis 等后续主题。

用户已明确要求：

> **讲解内容不要脱离当前主线。**

因此 `context.Context` 必须始终放回：

```text
HTTP Request
→ Handler
→ Service
→ Repository
```

来讲。

---

# 已建立的前置心智模型

以下不需要机械从头复习，除非用户主动表示忘记。

## HTTP / Router / Auth

```text
Method + Route Pattern
→ Handler

Credential
→ Authentication
→ Principal
→ Authorization
```

已建立 404 / 405、401 / 403、Principal / tenant 的第一轮理解。

## Middleware

已建立：

```text
Middleware
= 包住下一层 Handler 的公共逻辑

next.ServeHTTP(w, r)
= 把当前请求交给下一层

启动时组装
请求时从外向内执行
return 后从内向外返回
```

尚缺独立小改和 chain 截断故障实验。

---

# 第 4 章 Handler → Service → Repository：当前已建立

主项目：

- [`../exercises/go-ticket-api/`](../exercises/go-ticket-api/)

已经顺过真实：

```text
Create Ticket
Handler.create
→ Service.Create
→ Repository.Create
→ MemoryRepository
→ map
```

```text
Get Ticket
Handler.get
→ Service.Get
→ Repository.Get
→ map
→ Ticket / ErrNotFound
→ Service
→ Handler
```

```text
Close Ticket
Handler.close
→ Service.Close
→ Service.Get
→ Repository.Get
→ 业务状态 / Version 检查
→ open -> closed
→ Repository.Update
→ map
```

当前理解：

```text
Handler
= HTTP 输入 / 输出适配

Service
= 当前业务用例负责人，组织步骤、执行业务规则、修改状态

Repository
= Service 读写业务事实的数据访问边界

MemoryRepository
= 当前 Repository 的具体内存实现
```

已建立：

```text
map[string]Ticket ≈ Python dict[str, Ticket]
Create / Get / Update
TenantID scope
Repository -> Service -> Handler 的成功值 / error 反向返回
Service.Close 的业务状态转换
Version / expectedVersion
optimistic conflict / lost update 第一轮模型
RWMutex：RLock / Lock
defer Unlock
RWMutex 与 Version 解决不同问题
```

这些仍主要是对话理解证据。

---

# 当前精确话题：`context.Context`

当前不要再从“ctx 是什么缩写”开始，而是从下面已经建立的模型继续。

## 1. `ctx` 是上下文，但当前最重要是请求生命周期

用户已经理解：

> `ctx` = context / 上下文；在当前 HTTP 主线里，可以把它看作这一次请求的**生命周期信号载体 / 生命线**。

需要保持一个精确修正：

```text
ctx 不保证请求一定正常或成功
ctx 负责携带 / 传播请求生命周期状态
```

当前最重要的内容：

```text
cancel
= 请求被取消

deadline / timeout
= 时间预算耗尽

request-scoped value
= 少量跟随这次请求传播的信息，例如 Principal
```

业务参数（title、ticketID、tenantID、expectedVersion 等）仍应正常作为函数参数传，不要都塞进 Context。

---

## 2. `ctx` 从哪里来

真实 Handler 中：

```go
h.service.Create(r.Context(), principal.TenantID, input)
```

当前理解：

```text
net/http 收到一次 HTTP Request
↓
*http.Request 自带 Request Context
↓
Handler 用 r.Context() 拿出来
↓
传给 Service
↓
Service 再把同一请求关系传给 Repository
```

所以：

```text
r.Context()
→ Handler
→ Service(ctx)
→ Repository(ctx)
```

Service 不应该无缘无故改成 `context.Background()`，否则会切断上游请求的取消 / deadline 传播关系。

---

## 3. Authentication 还会基于原 Context 派生新 Context

已经看过真实：

```go
ctx := context.WithValue(r.Context(), principalContextKey{}, principal)
next.ServeHTTP(w, r.WithContext(ctx))
```

当前最小模型：

```text
原 Request Context
├─ cancel / deadline 生命周期
↓ 派生
新 Context
├─ 保留上游生命周期关系
└─ 附加 Principal
```

之后 Handler：

```go
principalFromContext(r.Context())
```

可以读到 Authentication Middleware 放进去的 Principal。

不要扩展成“所有业务参数都放 ctx”。

---

## 4. `ctx.Err()` 已讲到

仓库 MemoryRepository 真实代码：

```go
if err := ctx.Err(); err != nil {
    return Ticket{}, err
}
```

用户已补齐 Go 基础：

```text
nil
≈ Python None 的当前阅读类比
```

因此：

```text
ctx.Err() == nil
= 当前 Context 还没有因为 cancel / deadline 结束

ctx.Err() != nil
= Context 已经结束，需要看结束原因
```

可能的生命周期错误：

```text
context.Canceled
context.DeadlineExceeded
```

必须区分：

```text
ErrNotFound / ErrVersionConflict
= 业务 / 数据语义错误

context.Canceled / context.DeadlineExceeded
= 请求生命周期结束原因
```

`ctx` 不是用来储存所有 Service / Repository 业务错误的。

---

## 5. `ctx.Done()` 已讲到

当前最小模型：

```text
ctx.Err()
= 现在检查：已经结束了吗？为什么？

ctx.Done()
= 如果以后结束，通知我
```

对于当前快速 MemoryRepository：

```text
开始前检查 ctx.Err()
→ 很快操作 map
```

已经足够用来理解代码。

但对于未来 Slow Repository / DB / downstream 等需要等待的操作：

```text
工作完成
vs
ctx.Done()
```

需要能够等待“谁先发生”。

当前只做了概念性 `select` 预览：

```go
select {
case <-workDone:
    // 工作完成
case <-ctx.Done():
    return ctx.Err()
}
```

不要把这视为已经掌握 channel / select 语法。

当前理解：

```text
ctx.Done()
= 生命周期结束通知

ctx.Err()
= 生命周期为什么结束
```

---

# Context error 如何回到上层

已经重新连接到之前学过的错误返回链：

```text
Repository
→ context.Canceled / DeadlineExceeded
↑
Service
→ 不继续业务逻辑，把 error 向上返回
↑
Handler
→ 决定 HTTP 世界怎样表达
```

当前教学代码的 `handleError` 尚未专门映射 Context error；不要在这里提前背 408 / 499 / 504 等生产策略，后面 Error / Timeout 章节再根据真实边界讨论。

---

# 当前能力证据判断

```text
Handler / Service / Repository：L2 对话模型正在成形
MemoryRepository Create/Get/Update：已建立对话理解
Tenant boundary：已建立对话理解
Version / optimistic conflict：第一轮模型已建立
RWMutex / defer：能沿真实代码解释用途
context.Context propagation：第一轮模型已建立
ctx.Err / nil / Canceled / DeadlineExceeded：能沿主线解释
ctx.Done：已理解“结束通知”用途，但尚无代码实验
Go 独立实现：仍缺证据
```

仍然不要标 L3。

---

# 下一位老师从这里直接继续

不要重新讲：

```text
Repository 是什么
Memory map 是什么
ctx 是什么缩写
nil 是什么
ctx.Err() 和 ctx.Done() 的基本区别
```

当前最后一个自然问题是：

> **这个 timeout / deadline 到底是谁设置进去的？为什么有的 `r.Context()` 有 deadline，有的没有？**

直接沿主线讲：

```text
HTTP Request
↓
r.Context()
↓
Handler
↓
Service
↓
Repository
```

推荐下一小节顺序：

1. `deadline` 是一个什么时刻 / 时间预算；
2. 谁可以基于现有 ctx 创建带 timeout / deadline 的派生 Context；
3. `cancel()` 为什么要调用；
4. timeout 到点后 `Done()` / `Err()` 怎样变化；
5. 再做 Slow Repository 的真实等待模型；
6. 最后故意把 Service 改成 `context.Background()`，观察为什么取消链会断。

讲解仍然必须围绕当前 Ticket API 调用链，不开独立 Go Context 语法课。

---

# 当前一句话接棒

> **用户已经沿 `Handler → Service → Repository` 把 `context.Context` 接回真实请求链：知道 `ctx` 是上下文，在当前主线里最重要是传播请求 cancel/deadline 生命周期；`r.Context()` 来自 HTTP Request，Authentication 可用 `WithValue` 派生并附加 Principal，Handler 把 ctx 传给 Service，Service 再传给 Repository；`ctx.Err()==nil` 表示当前没有因取消/超时结束，`Canceled/DeadlineExceeded` 是生命周期错误；`ctx.Done()` 是未来结束通知，`ctx.Err()` 给结束原因。当前下一步讲 timeout/deadline 谁设置、怎么到点，再进入 Slow Repository 取消实验。**
