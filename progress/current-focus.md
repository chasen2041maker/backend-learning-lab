# 当前学习接棒点

最后更新：2026-09-01

这份文件是**新的 ChatGPT / Codex / 其他账号最优先读取的精确接棒入口**。

> 目标：新会话不依赖旧聊天记录，只读仓库就能知道用户已经学到哪里、哪些只是听懂、下一步从哪里继续、应该用什么教学方式。

长期能力地图见：

- [`../LEARNER_PROFILE.md`](../LEARNER_PROFILE.md)
- [`../GO_BACKEND_TRACK.md`](../GO_BACKEND_TRACK.md)
- [`../GROWTH_PATH.md`](../GROWTH_PATH.md)

最近详细学习记录：

- [`2026-08-31.md`](2026-08-31.md)：Repository / MemoryRepository / Version / RWMutex；
- [`2026-09-01.md`](2026-09-01.md)：Context 请求生命周期传播、`Err()` / `Done()`；
- [`2026-09-01-final.md`](2026-09-01-final.md)：`WithTimeout` / `WithDeadline`、Slow Repository、`context.Background()` 断链与跨账号最终接棒。

---

# 一、学习者与教学方式

当前长期有效定位：

```text
Python / Agent 应用经验相对更强
Go 语法与传统后端工程仍是主要短板
```

不要把“已经听懂某段真实 Go 代码”误判成“已经可以独立写 Go”。

默认教学方式必须保持：

```text
1. 先讲这段代码解决什么真实后端问题
2. 沿请求 / 数据 / 状态变化讲谁调用谁
3. 说明失败怎么传播
4. Go 语法挡住理解时，再局部用 Python 类比拆语法
5. 回到真实 Go 代码
```

用户已明确要求：

> **讲解不要脱离当前主线。**

不要把教学变成：

```text
抽象 Go 语法课
→ interface / struct / channel / Context 名词堆砌
→ 脱离 Ticket API 出小动物之类的语法题
```

也不要强迫从空白目录重写整套项目。

---

# 二、前置内容：不要机械重讲

除非用户主动表示忘记，否则以下只需快速连接，不要从头长篇复习。

## HTTP / Router / Auth

已建立第一轮：

```text
Method + Route Pattern
→ Handler

Credential
→ Authentication
→ Principal
→ Authorization
```

能区分第一轮：

```text
404 / 405
401 / 403
Authorization Header / Credential
Principal / tenant
```

网络主线已有：

```text
Client
→ DNS
→ IP + Port
→ TCP / TLS
→ OS / Socket
→ Go process
→ net/http
→ *http.Request
```

## Middleware

已建立 L2 初步对话模型：

```text
Middleware
= 包住下一层 Handler 的公共逻辑

next.ServeHTTP(w, r)
= 把当前请求交给下一层

启动时组装
请求时从外向内执行
return 后从内向外返回
```

已经理解 `HandlerFunc`、匿名函数、闭包的第一轮关系。

仍缺：独立小改 + chain 截断故障实验，所以不标 L3。

---

# 三、第 4 章 Handler → Service → Repository：已建立的主线

主项目：

- [`../exercises/go-ticket-api/`](../exercises/go-ticket-api/)

已经顺过真实请求：

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
→ 状态 / Version 检查
→ open -> closed
→ Repository.Update
→ map
```

当前职责理解：

```text
Handler
= HTTP 输入 / 输出适配

Service
= 当前业务用例负责人，组织步骤、执行业务规则、修改业务状态

Repository
= Service 读写业务事实的数据访问边界

MemoryRepository
= 当前 Repository 的具体内存实现
```

已纠正：

```text
不是 Repository 调真正的业务逻辑
而是 Service 组织业务逻辑，再调用 Repository 读写数据
```

## MemoryRepository / map

已能沿真实代码理解：

```go
r.tickets[value.ID] = value
```

最小模型：

```text
map[string]Ticket
≈ Python dict[str, Ticket]

Create
= 放入 map

Get
= 从 map 读取

Update
= 检查当前值后用新 Ticket 覆盖旧值
```

已明确：map 在 Go 进程内存中，进程重启数据消失。

## Tenant boundary

已理解：

```go
if !ok || value.TenantID != tenantID {
    return Ticket{}, ErrNotFound
}
```

并连接：

```text
Authentication
→ Principal.TenantID
→ Handler
→ Service
→ Repository tenant scope
```

## 返回链 / error

已建立：

```text
调用：Handler → Service → Repository
返回：Repository → Service → Handler
```

成功值和 error 都沿调用栈返回。

## Service.Close

已顺过：

```text
Get 当前 Ticket
→ 是否已 closed
→ expectedVersion 是否有效
→ 当前 Version 是否匹配
→ open -> closed
→ Version + 1
→ UpdatedAt
→ Repository.Update
```

已经开始真正理解 Service 不是单纯中转层。

## Version / optimistic conflict

第一轮模型已建立：

```text
读数据
→ 做业务判断
→ 真正写入
```

中间别人可能先更新。

因此 Repository 写入前再比较：

```text
current.Version
vs
expectedVersion
```

不一致：

```text
→ ErrVersionConflict
→ 防止旧数据覆盖新数据
```

已讲 `lost update` / optimistic locking 的真实问题，但尚未进入 PostgreSQL 实现。

## RWMutex / defer

已能沿真实代码解释：

```go
r.mu.RLock()
defer r.mu.RUnlock()
```

```go
r.mu.Lock()
defer r.mu.Unlock()
```

当前最小模型：

```text
RLock
= 读锁，多读者可以并行

Lock
= 写锁，写入时独占

defer Unlock
= 函数退出前保证释放锁
```

必须保持区分：

```text
RWMutex
= 当前 Go 进程内共享 map 的并发访问安全

Version
= 业务层面的旧数据覆盖保护
```

---

# 四、当前精确话题：`context.Context`

当前已经讲到 L2 初步对话模型，不要从“ctx 是什么缩写”重新开始。

始终放回：

```text
HTTP Request
→ Handler
→ Service
→ Repository
```

## 1. Context 当前核心定义

用户当前可以把：

```text
ctx = context / 上下文
```

理解成：

> **在当前 HTTP 主线里，ctx 是这次请求的生命周期信号载体 / 生命线。**

必须保留精确修正：

```text
ctx 不保证请求一定成功
ctx 负责携带 / 传播请求生命周期状态
```

当前主要内容：

```text
cancel
= 请求被取消

deadline / timeout
= 时间预算耗尽

request-scoped value
= 少量随请求传播的信息，例如 Principal
```

业务参数仍显式传递。

## 2. ctx 从哪里来

真实 Handler：

```go
h.service.Create(r.Context(), principal.TenantID, input)
```

当前理解：

```text
net/http 收到 HTTP Request
↓
*http.Request 自带 Request Context
↓
Handler 用 r.Context() 取得
↓
传给 Service
↓
Service 继续传给 Repository
```

所以：

```text
r.Context()
→ Handler
→ Service(ctx)
→ Repository(ctx)
```

不是每层各造一个 Context。

## 3. Authentication / WithValue

已看真实：

```go
ctx := context.WithValue(r.Context(), principalContextKey{}, principal)
next.ServeHTTP(w, r.WithContext(ctx))
```

当前模型：

```text
父 Request Context
├─ cancel / deadline
↓ 派生
子 Context
├─ 继续受父生命周期影响
└─ 附加 Principal
```

Context value 不是万能业务参数袋。

## 4. `nil`

Go 基础已补：

```text
nil
≈ 当前阅读时可类比 Python None
```

所以：

```text
err == nil
= 没有 error

err != nil
= 有 error
```

## 5. `ctx.Err()`

仓库真实：

```go
if err := ctx.Err(); err != nil {
    return Ticket{}, err
}
```

当前理解：

```text
ctx.Err() == nil
= Context 当前没有因为取消 / deadline 结束

context.Canceled
= 被取消

context.DeadlineExceeded
= 时间预算耗尽
```

必须区分：

```text
ErrNotFound / ErrVersionConflict
= 业务 / 数据语义 error

Canceled / DeadlineExceeded
= Context 生命周期结束原因
```

ctx 不是保存所有业务错误的地方。

## 6. `ctx.Done()`

已建立：

```text
ctx.Err()
= 现在检查：已经结束了吗？为什么？

ctx.Done()
= 将来结束时通知我
```

概念预览过：

```go
select {
case <-workDone:
    // 工作完成
case <-ctx.Done():
    return ctx.Err()
}
```

当前只理解用途，不代表已经掌握 channel / select。

## 7. Context error 仍走原返回链

```text
Repository
→ Canceled / DeadlineExceeded
↑
Service
→ 不继续业务逻辑，继续返回 error
↑
Handler
→ 决定 HTTP 如何表达
```

当前教学代码的 Handler 尚未专门映射 Context error；不要提前背生产状态码策略。

## 8. `WithTimeout` / `WithDeadline`

已讲到：原始 `r.Context()` 不一定带业务想要的明确 deadline。

拿到父 ctx 的代码可以基于它派生子 ctx：

```go
ctx, cancel := context.WithTimeout(parentCtx, 2*time.Second)
defer cancel()
```

当前理解：

```text
WithTimeout
= 还能活多久

WithDeadline
= 最晚活到哪个时间点
```

父子关系：

```text
父 ctx 先结束
→ 子 ctx 一起结束

子 timeout/deadline 先到
→ 子 ctx 自己结束
```

## 9. `cancel()`

当前最小模型：

```text
cancel()
= 主动声明这个派生 Context 对应的工作不再需要继续
```

即使 timeout 尚未到，工作提前结束时也应释放派生 Context 相关资源。

已和：

```go
Lock()
defer Unlock()
```

建立“提前登记清理动作”的类比。

但还没有独立写代码。

## 10. Slow Repository 模型

已讲：

```text
Repository 工作 3 秒
上游 timeout 1 秒
```

错误模型：

```go
time.Sleep(3 * time.Second)
```

只在开始检查一次 `ctx.Err()` 不够，因为 Context 不会魔法强杀普通阻塞代码。

重要结论：

> **Context 发出停止信号；底层代码 / API 必须主动支持和响应它。**

对于慢操作，需要等待：

```text
工作完成
vs
ctx.Done()
```

谁先发生。

## 11. `context.Background()` 断链

已经讲通：

正确：

```go
s.repository.Get(ctx, tenantID, id)
```

错误主线示例：

```go
s.repository.Get(context.Background(), tenantID, id)
```

当前理解：

```text
Background
= 独立根 Context 的最小阅读模型
```

如果 Service 丢掉上游 Request ctx：

```text
Client cancel / request timeout
↓
Handler / Service 上游知道
✂
Repository 收不到原请求的生命周期结束信号
```

因此可能继续做无意义工作。

同时已明确：`context.Background()` 不是永远不能用；真正独立于某个 HTTP Request 的根任务可以从根 Context 开始。

---

# 五、当前能力证据判断

```text
HTTP / 网络：L2 初步
http.Handler / HandlerFunc：L2 初步
Middleware：L2 初步对话理解，缺实践
Handler / Service / Repository：L2 对话模型已较完整，缺实践
MemoryRepository Create/Get/Update：已建立对话理解
Tenant boundary：已建立对话理解
Version / optimistic conflict：第一轮模型已建立
RWMutex / defer：能沿真实代码解释，缺独立实现
context.Context propagation：L2 初步对话理解
ctx.Err / Done / nil / Canceled / DeadlineExceeded：可沿真实主线解释
WithTimeout / WithDeadline / cancel：已建立第一轮模型
Slow Repository cancellation：概念模型已建立，未运行
context.Background() 断链：概念模型已建立，未运行
Go 独立实现：仍缺证据
```

仍然不要标 L3。

第 4 章仍缺：

```text
[ ] 独立完成一个小变化
[ ] 补 / 改 test
[ ] 主动制造 conflict / 分层错误并解释
```

Context 仍缺：

```text
[ ] 真正实现 Slow Repository
[ ] timeout / deadline test
[ ] client cancel test
[ ] context.Background() 断链对比实验
```

---

# 六、换账号后的精确下一步

新的老师不要重新讲：

```text
Repository 是什么
Memory map 是什么
Version / RWMutex 基本模型
ctx 是什么缩写
nil 是什么
ctx.Err() / ctx.Done() 基本区别
WithTimeout / WithDeadline 基本意义
Slow Repository 为什么要响应 Context
context.Background() 为什么会断链
```

## 第一问直接从这里开始

> **cancel 到底是谁触发的？HTTP Request 自身的取消，和 `WithCancel` / `WithTimeout` 返回给我们代码的 `cancel()`，分别是谁负责触发？**

继续沿：

```text
Client
→ HTTP Request
→ r.Context()
→ Handler
→ Service
→ Repository
```

推荐接下来顺序：

1. `r.Context()` 在客户端断开、请求结束等情况下，谁负责取消；
2. `WithCancel` / `WithTimeout` 返回的 `cancel` 是谁调用；
3. 为什么派生 Context 的创建者通常负责 `defer cancel()`；
4. 把 Slow Repository 变成可运行实验；
5. 观察 timeout 时 `Done()` / `Err()`；
6. 故意改成 `context.Background()`，验证取消链断开；
7. 补测试，把 Context 从 L2 对话理解推进到 L3 控制能力。

---

# 七、给下一位 GPT / Codex 的一句话

> **用户已经沿 `Handler → Service → Repository` 把第 4 章和 Context 自然接起来：Repository/Memory map/Create/Get/Update、tenant scope、Service.Close、Version/lost update、RWMutex/defer 已形成 L2 对话模型；Context 已讲到 Request ctx 传播、WithValue Principal、nil、Err/Done、Canceled/DeadlineExceeded、WithTimeout/WithDeadline、defer cancel、Slow Repository 取消模型和 `context.Background()` 断链。尚未做独立代码/测试，所以不标 L3。下一次不要复习定义，直接讲“HTTP Request 自动 cancel vs 派生 Context 手动 cancel 是谁触发”，随后做 Slow Repository timeout/cancel/Background 断链实验。教学必须围绕真实 Ticket API 调用链，Go 语法挡住时局部用 Python 类比。**
