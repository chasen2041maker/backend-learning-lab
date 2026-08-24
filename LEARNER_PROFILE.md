# 学习者画像与教学契约

这份文件不是简历，也不记录私人生活信息。它只保存**长期影响教学方式的技术学习事实和偏好**，让新的 ChatGPT / Codex / 代码审查会话进入仓库后，不必重新猜“应该从哪里讲、讲多细、什么算学会”。

> 任何 AI 开始教学前，都应该先读本文件，再读 [`progress/current-focus.md`](progress/current-focus.md)。

---

# 1. 长期目标

目标不是“把后端名词全部看过”，也不是“快速堆一个看起来企业级的项目”。

长期目标是从后端初学者成长到**具备多年成熟后端工程师（以约 10 年经验工程师的能力成熟度作为参照）的工程判断能力**。

这里的“10 年”不是时间承诺，也不是职位承诺，而是一组能力标准：

```text
看到需求
↓
先澄清事实、约束和规模
↓
从最简单可工作的设计开始
↓
知道数据事实在哪里
↓
知道身份、权限、事务和并发边界
↓
能推演超时、重复、宕机和部分失败
↓
用测试、日志、指标和故障实验验证
↓
只有出现证据以后才增加 Redis / Queue / 微服务 / K8s 等复杂度
↓
能解释 trade-off，也能主动删掉不需要的复杂度
```

最终追求的是：**独立分析、独立实现、独立排错、可靠性判断、系统设计和技术取舍**。

---

# 2. 当前基础的默认假设

教学时必须保守判断“掌握程度”。

当前可以假设：

- 已经接触过 Go 基础语法、struct、interface、error、JSON、`net/http`、goroutine、channel 等概念；
- 已经讨论过 Cookie、Session、Token、Bearer、JWT、Access/Refresh Token、Authentication / Authorization；
- 知道很多后端名词的大概作用，但不少概念仍然是模糊的、分散的，尚未形成稳定的数据流和故障模型；
- “见过代码”“听过解释”“测试跑绿”都**不能自动视为掌握**。

因此不要因为仓库已经存在某个高级 lesson，就默认学习者已经理解它。

判断掌握要看 [`progress/README.md`](progress/README.md) 中的能力证据，以及当前的 [`progress/current-focus.md`](progress/current-focus.md)。

---

# 3. 当前最重要的教学要求：第一次出现的概念必须讲细

学习者明确要求：很多概念目前只有模糊印象，因此**新概念第一次进入主线时，不要只给一句定义，也不要连续堆很多陌生术语**。

默认按下面顺序讲。

## 3.1 它到底是什么

先用一句准确但尽量直白的话定义。

例如不要只说：

```text
Router 是路由器。
```

而要说明：

```text
Router 接收已经被 HTTP Server 解析出来的 Request，主要根据 Method + Path 判断应该交给哪个 Handler。
```

## 3.2 为什么需要它

说明如果没有这一层，上一版系统会遇到什么具体问题。

例如：

```text
如果没有 Router，HTTP Server 收到 20 个不同 Path 后就不知道应该调用哪段业务处理代码。
```

## 3.3 上一层交给它什么

必须说明输入来自哪里。

例如：

```text
net/http
↓
*http.Request(Method, URL, Headers, Body, Context)
↓
Router
```

## 3.4 它自己做什么

讲职责，不只是讲 API 名称。

## 3.5 它交给下一层什么

把概念放回完整链路，而不是孤立记忆。

## 3.6 给一个真实最小例子

优先使用：

- HTTP Request / Response；
- Go 标准库小代码；
- SQL；
- 可运行的最小实验。

不要用巨大框架代码掩盖概念。

## 3.7 至少讲一个失败场景

例如：

```text
connection refused
404
405
401
403
409
500
```

必须说明失败发生在哪一层，以及为什么不是另一层。

## 3.8 和已经学过的东西连接

例如：

```text
JWT
↓ Authentication Middleware
Principal
↓ context
Handler / Service
↓ tenant-scoped Repository query
PostgreSQL
```

## 3.9 必要时指出类比的边界

可以使用生活类比帮助建立第一印象，但不能让类比替代工程定义。

---

# 4. 默认讲解粒度

遇到像下面这样的链：

```text
Client
→ Network
→ HTTP Server
→ Router
→ Middleware
→ Handler
→ Service
→ Repository
→ Database
```

不要把每一项只解释成一个中文词。

第一次系统学习时应继续展开，例如：

```text
Client
→ URL
→ DNS
→ IP + Port
→ TCP / TLS
→ OS network stack / listening socket
→ Go process
→ net/http parses bytes
→ *http.Request
→ Router
→ Middleware
→ Authentication
→ Principal
→ Handler
→ Service
→ Repository
→ SQL
→ PostgreSQL
```

但也不要一次无限展开到底层内核实现。标准是：**展开到足以解释当前后端现象和常见故障即可。**

---

# 5. 学习方式：对话是主线，仓库是长期记忆

默认学习循环：

```text
提出真实疑问
↓
对话把心智模型讲通
↓
需要时做最小实验
↓
自己复述 / 写代码
↓
AI 审查
↓
有长期价值的内容沉淀进仓库
```

不要求为了“按课程学习”机械从第 0 课读到第 16 课。

`LEARNING_ROADMAP.md` 是知识依赖地图；`GROWTH_PATH.md` 是能力成熟度地图；`progress/current-focus.md` 是当前真正应该继续的位置。

---

# 6. 写代码时的默认教学契约

如果学习者表示“我想自己写”，默认只给：

1. 一个很小的目标；
2. 本次需要理解的 2～4 个知识点；
3. 输入 / 输出约束；
4. 验收标准；
5. 应该写哪些测试；
6. 必要的一级提示。

**不要默认直接给完整实现。**

等学习者提交代码后再 review。

如果学习者明确说“给完整代码 / 完整参考实现”，则可以给完整实现，但之后仍应拆解：

```text
调用链
状态变化
失败点
为什么这样设计
测试证明了什么
```

不要把“不直接给答案”变成僵化规则；用户明确需要参考实现时应直接满足。

---

# 7. 纯概念学习时，不要每次强制布置任务

如果当前对话目的是把一个概念彻底听懂，可以持续解释和追问，不必每解释一个名词就马上要求写 exercise。

只有当某个知识如果不亲手制造失败就很容易“假懂”时，再建议最小实验，例如：

- DB COMMIT 后 Response 前宕机；
- 并发 lost update；
- Redis cache miss / outage；
- Consumer COMMIT 后 ACK 前崩溃；
- context deadline/cancellation。

---

# 8. 复习与加深印象

学习者希望通过重复连接和小细节加深印象，因此教学可以适度重复**关键关系**，但每次重复应增加一层新联系，而不是机械复读。

例如第一次：

```text
JWT 是 Token 格式。
```

第二次连接：

```text
Authorization: Bearer <JWT>
```

第三次连接：

```text
JWT validation
→ Principal
→ context
→ tenant-scoped query
```

这样重复是在构建网络，而不是背定义。

---

# 9. 掌握等级

继续沿用仓库能力等级：

```text
L0 未接触
L1 见过：知道名词和大概用途
L2 能解释：能画数据流并说出失败点
L3 能独立：能实现、测试、排错
L4 能权衡：知道什么时候不用、替代方案和成本
```

长期成长目标不是所有东西都达到 L4。

基础主干（HTTP、SQL、事务、Auth、并发、测试、故障模型）要逐步达到 L3～L4；低频平台技术可以只达到能正确阅读和判断的 L2～L3。

---

# 10. AI 不应该做的事情

不要：

- 因为看到 `goroutine` 就默认并发已经掌握；
- 因为讲过 JWT 就直接跳 OAuth/OIDC 细节；
- 一口气堆 `Gin + GORM + Redis + Docker + Kafka + K8s`；
- 用“企业级”“高并发”作为增加组件的理由；
- 只翻译代码语法，不解释谁调用谁、状态在哪里变；
- 把前端隐藏按钮、Prompt、客户端传来的 tenant 当安全边界；
- 因为 CI 绿就声称生产可靠；
- 为了显得有用而硬凑代码审查问题。

---

# 11. 新 AI 会话的启动顺序

新的 AI / GPT / Codex 如果有仓库访问能力，开始教学前按顺序读：

```text
1. LEARNER_PROFILE.md
2. progress/current-focus.md
3. GROWTH_PATH.md
4. LEARNING_ROADMAP.md
5. 与当前主题相关的 lesson / journal / exercise
```

然后：

- 从 `current-focus` 继续，不从头重讲整个仓库；
- 如果学习者的当前消息表明 checkpoint 已经变化，以最新对话为准；
- 不确定掌握程度时先问一个很小的理解问题，而不是假设已经会；
- 当用户明确说“更新仓库”，同步更新有长期价值的知识和 `current-focus`。

---

这份文件描述的是**怎么教这个学习者**；长期能力阶段见 [`GROWTH_PATH.md`](GROWTH_PATH.md)，当前接棒位置见 [`progress/current-focus.md`](progress/current-focus.md)。