# 当前学习接棒点

最后更新：2026-09-05

这份文件是新的 ChatGPT / Codex / 其他账号继续教学时最优先读取的精确入口。

> 目标：不要依赖旧聊天记录，不要机械从头复习；先确认这里记录的当前模型，再从“下一步”继续。

长期地图：

- [`../LEARNER_PROFILE.md`](../LEARNER_PROFILE.md)
- [`../GO_BACKEND_TRACK.md`](../GO_BACKEND_TRACK.md)
- [`../GROWTH_PATH.md`](../GROWTH_PATH.md)

最近详细记录：

- [`2026-08-31.md`](2026-08-31.md)：Repository / MemoryRepository / Version / RWMutex；
- [`2026-09-01.md`](2026-09-01.md)：Request Context 传播、`Err()` / `Done()`；
- [`2026-09-01-final.md`](2026-09-01-final.md)：Timeout / Deadline / Slow Repository / `Background()` 断链；
- [`2026-09-03.md`](2026-09-03.md)：cancel 来源、数据库响应 Context、Repository interface / 多态 / DI；
- [`2026-09-05.md`](2026-09-05.md)：**校正：FakeRepository 尚未学习，下一次必须从这里重新开始。**

---

# 一、教学方式必须保持

当前主要短板仍是 Go 语法和传统后端工程边界；不要把“能沿真实代码解释”误判成“可以独立从空白实现”。

默认方式：

```text
真实后端问题
→ 请求 / 数据 / 状态怎么流
→ 谁调用谁、谁返回谁
→ 失败怎么传播
→ Go 语法挡住时局部用 Python 类比
→ 回到真实 Go 代码
```

不要把课程变成脱离 Ticket API 的抽象 Go 语法课，也不要强迫从空白重写整套项目。

---

# 二、前置内容：除非用户主动忘记，否则不要长篇重讲

## HTTP / Router / Auth

```text
Method + Route Pattern → Handler
Credential → Authentication → Principal → Authorization
```

已建立 404/405、401/403、Authorization Header、Principal/Tenant 第一轮模型。

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
Middleware = 包住下一层 Handler 的公共逻辑
next.ServeHTTP(w, r) = 把当前请求交给下一层
启动时组装
请求时外 → 内执行
return 后内 → 外返回
```

已理解 `HandlerFunc`、匿名函数、闭包第一轮关系；仍缺独立小改和 chain 截断实验，因此不标 L3。

---

# 三、Handler → Service → Repository 主线：当前已经讲到哪里

主项目：[`../exercises/go-ticket-api/`](../exercises/go-ticket-api/)

已经顺过：

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
→ MemoryRepository.Get
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
→ open → closed
→ Version + 1
→ Repository.Update
→ map
```

当前职责模型：

```text
Handler
= HTTP 输入 / 输出适配

Service
= 当前业务用例负责人；组织步骤、执行业务规则、修改业务状态

Repository
= Service 读写业务事实的数据访问边界 / 能力合同

MemoryRepository
= Repository 的当前内存实现
```

已经纠正：

```text
不是 Repository 调业务逻辑
而是 Service 组织业务逻辑，再调用 Repository 读写事实
```

## MemoryRepository / map

已能解释：

```go
r.tickets[value.ID] = value
value, ok := r.tickets[id]
```

```text
map[string]Ticket ≈ Python dict[str, Ticket]
Create = 放入 map
Get = 从 map 读取
Update = 校验后覆盖当前 Ticket
```

map 属于 Go 进程内存，进程重启数据消失。

## Tenant / Version / RWMutex

已建立：

```text
Principal.TenantID
→ Handler
→ Service
→ Repository tenant scope
```

跨 tenant 查询对外仍可表现为 `ErrNotFound`，避免泄露资源存在性。

已讲：

```text
current.Version vs expectedVersion
不一致 → ErrVersionConflict
```

目的是防止旧数据覆盖新数据（lost update / optimistic conflict）。

必须继续区分：

```text
RWMutex
= 当前 Go 进程内共享 map 的并发访问安全

Version
= 业务层旧版本覆盖保护
```

---

# 四、`context.Context`：已经讲到的精确模型

不要重新从“ctx 是什么缩写”开始。

## 传播链

```text
HTTP Request
→ r.Context()
→ Handler
→ Service(ctx)
→ Repository(ctx)
→ 支持 Context 的 DB / downstream API
```

Context 当前可理解为这次请求的生命周期信号载体 / 取消与时间预算广播线；它不保证业务成功，也不是业务参数袋。

Authentication 已通过：

```go
ctx := context.WithValue(r.Context(), principalContextKey{}, principal)
next.ServeHTTP(w, r.WithContext(ctx))
```

派生子 Context，保留父生命周期关系并附加 Principal。

## `Err()` / `Done()`

```text
ctx.Err()
= 现在检查 Context 是否已结束，以及为什么

ctx.Done()
= 将来结束时的通知
```

已能区分：

```text
context.Canceled
context.DeadlineExceeded
```

和业务错误：

```text
ErrNotFound
ErrVersionConflict
```

Context error 仍沿原调用栈返回：

```text
Repository → Service → Handler
```

## Timeout / Deadline / cancel

```text
WithTimeout
= 子工作还能活多久

WithDeadline
= 子工作最晚活到哪个时间点

cancel()
= 创建者主动结束派生 Context / 释放相关资源
```

父子关系已建立：

```text
父 ctx 先结束 → 子 ctx 一起结束
子 timeout/deadline 先到 → 子 ctx 自己结束
子 cancel 不会反向取消父 ctx
```

## cancel 来源

已经讲清两类来源：

```text
A. r.Context()
Client 断开 / Request 生命周期结束
→ net/http 管理并取消 Request Context

B. 派生 Context
WithCancel / WithTimeout 返回 cancel
→ 创建派生 Context 的代码通常负责 defer cancel()
```

还明确：

```text
Context 自己结束
≠ 普通 Go 代码被强制杀死
```

Context 发信号；底层代码/API必须支持并响应它。

## Slow Repository / Database

已讲概念模型：

```text
Repository 工作 3 秒
上游 timeout 1 秒
```

普通：

```go
time.Sleep(3 * time.Second)
```

不会被 Context 自动强杀。

支持 Context 的慢操作需要等待：

```text
工作完成
vs
ctx.Done()
```

真实数据库调用应优先使用类似：

```go
db.QueryContext(ctx, ...)
db.ExecContext(ctx, ...)
```

使请求取消 / deadline 有机会传到真正耗资源的 DB 工作。

已理解：如果 DB 已经成功 COMMIT，之后 Context cancel 不会自动撤销已提交事实；这会在 Transaction / Idempotency 阶段继续展开。

## `context.Background()`

已讲通：在 HTTP Request 主线中无故改成 `context.Background()` 会切断上游 cancel/deadline 传播；但真正独立于 Request 的根任务可以合理使用根 Context。

**仍缺所有实际 Context 实验和测试。**

---

# 五、Repository interface / 多态 / DI：已学边界

这部分已经做过第一轮讲解，不要重新从 interface 定义开始。

## 1. `MemoryRepository` 实现 `Repository`

Go 是隐式实现：

```text
Repository interface 要求 Create / Get / List / Update

*MemoryRepository 拥有相同签名的方法
→ 自动满足 Repository
```

没有 `implements` 关键字。

## 2. Service 依赖接口而不是具体实现

真实结构：

```go
type Service struct {
    repository Repository
}
```

不是绑死：

```go
repository *MemoryRepository
```

当前理解：Service 只依赖 Repository 的能力合同，不关心底层当前具体实现。

## 3. interface value 里仍保存具体实现

当前阅读模型：

```text
Repository interface value
├─ dynamic type  = *MemoryRepository
└─ dynamic value = 当前具体 MemoryRepository 对象
```

因此：

```go
s.repository.Get(...)
```

虽然静态类型是 `Repository`，当前实际会动态调用：

```text
(*MemoryRepository).Get(...)
```

## 4. 小接口 / 消费者视角

已建立：

> interface 应优先表达“调用方真正需要什么能力”，不是把实现者所有方法全塞进去。

不要把“小接口”机械理解成接口越碎越好；当前 `Service` 确实使用 Create/Get/List/Update，所以当前 Repository 合同仍合理。

## 5. Dependency Injection

已经讲通最基础 DI：

```go
repository := NewMemoryRepository()
service := NewService(repository)
```

含义：

```text
Service 不自己偷偷 new MemoryRepository
↓
外部先创建依赖
↓
通过 NewService(repository Repository) 注入
```

已区分：

```text
启动阶段
= 组装依赖 / Handler 链

请求阶段
= 使用已组装好的 Service / Repository 处理 Request
```

---

# 六、重要：`FakeRepository` 明确尚未学习

**不要因为 2026-09-05 的上一条对话已经开始出现 FakeRepository 示例，就把它算作学过。**

用户已明确表示：

> **“用 FakeRepository 测 Service 这个我没学。”**

因此当前状态必须记录为：

```text
FakeRepository：未学习
FakeRepository 注入 Service：未学习
用 Fake 控制 Get 返回 Ticket / error：未学习
Service unit test：未学习
用 Fake 记录 Update 调用：未学习
Fake / Stub / Mock：未学习
```

下一位老师必须从 FakeRepository 的第一步重新讲，不能直接从更后的测试技巧继续。

---

# 七、当前能力判断

仍以对话理解证据为主：

```text
HTTP / Router / Auth：L2 初步
Middleware：L2 初步，缺实践
Handler / Service / Repository：L2 较完整，缺实践
MemoryRepository / tenant / Version / RWMutex：可沿真实代码解释
context.Context propagation / cancel / timeout：L2 初步，缺真实实验
Repository interface / 动态分派 / DI：L2 初步对话理解
FakeRepository / Service unit test：未学习
Go 独立实现：仍缺证据
```

不要标 L3。

---

# 八、下一次直接从哪里继续

不要重新讲：

```text
Repository 基础定义
Memory map 基本动作
Version / RWMutex 基本模型
Context 定义 / Err / Done / timeout / Background 基础
MemoryRepository 为什么满足 Repository
interface value 为什么能调用 MemoryRepository.Get
Dependency Injection 的基本定义
```

## 第一部分：从零开始讲 `FakeRepository`

**第一问直接从这里开始：**

> 为什么我们只想测试 `Service.Close` 的业务规则时，不一定希望真的启动 PostgreSQL / 使用真实数据库？

然后按这个顺序：

```text
1. 先说明真实测试问题，不先堆 Fake/Mock/Stub 术语
2. FakeRepository 是什么
3. 它为什么也是 Repository interface 的一个具体实现
4. NewService(fakeRepo) 为什么可以工作
5. Fake 如何预设 Get 返回 Ticket / error
6. 用真实 Service.Close 跑一条最小调用链
7. 再看 Fake 如何记录 Update 调用，验证 open → closed、Version + 1
```

沿真实调用链：

```text
Test
→ Service.Close
→ Repository interface
→ FakeRepository
→ 返回受控 Ticket / error
→ Service 执行业务规则
→ Test 断言结果
```

这部分讲完并确认理解后，再做一个最小 Go test。

## 第二部分：补 Context 实践

```text
SlowRepository
+ WithTimeout
+ ctx.Done()/ctx.Err()
+ context.Background() 断链对照
```

完成 FakeRepository / Service test 与 Context 实验后，再进入：

```text
PostgreSQL Repository
→ Transaction / Idempotency
```

---

# 九、给下一位老师的一句话

> **精确边界：用户已经理解 Handler → Service → Repository 主链、MemoryRepository/map、tenant、Version/RWMutex、Context cancel/timeout 概念，以及 `MemoryRepository implements Repository`、interface 动态具体类型、小接口和最基础 Dependency Injection；但用户在 2026-09-05 明确指出 `FakeRepository` 没学。上一位只是刚开始讲，不算学习完成。下一次必须从“为什么测试 Service 不一定启动数据库”开始，从零讲 FakeRepository，并沿真实 `Service.Close` 做最小测试；之后再补 SlowRepository timeout/Background 断链实验。**