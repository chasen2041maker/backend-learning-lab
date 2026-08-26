# Notes：快速定位、复习和对话学习沉淀

`notes/` 不和 `lessons/` 竞争。这里保存的是**导航、速查、术语和学习轨迹**。

如果一个主题需要完整解释“为什么、数据流、失败场景、生产边界”，去 `lessons/`；如果只是隔几周忘了关系、需要一分钟恢复，先来这里。

---

## 当前入口

### [`knowledge-map.md`](knowledge-map.md)

先看“这个概念在后端系统的哪一层”。

适合：

```text
我知道 Redis/JWT/Outbox 这些词
但不知道它们之间是什么关系
```

它不是详细教程，而是后端知识的地图。

### [`glossary.md`](glossary.md)

快速查词。

例如：

```text
Bearer 是什么？
Fencing Token 是什么？
Readiness 和 Liveness 什么区别？
```

术语表故意保持短；查完仍不理解因果链时去对应 lesson。

### [`authentication-cheatsheet.md`](authentication-cheatsheet.md)

Cookie / Session / Token / Bearer / JWT / Access Token / Refresh Token 的快速关系图。

适合已经学过、但隔一段时间容易重新混淆时使用。

### [`extended-topics.md`](extended-topics.md)

不是“还没学完的欠账清单”，而是技术扩展过滤器。

看到 Kafka、Sharding、ClickHouse、Service Mesh、IaC 等新名词时，先问：

```text
现在有什么真实问题？
当前简单方案为什么不够？
它会新增什么复杂度？
```

再决定是否进入主线。

### [`learning-journal/`](learning-journal/)

保存对话、调试、代码审查中真正建立或纠正的心智模型。

当前已有：

- [`2026-08-24-auth-jwt-session.md`](learning-journal/2026-08-24-auth-jwt-session.md)：登录、Session、Token、JWT 与后端信任边界；
- [`2026-08-24-github-app-write-scope.md`](learning-journal/2026-08-24-github-app-write-scope.md)：GitHub App/集成的写权限为什么和用户仓库权限不是一回事；
- [`2026-08-26-http-network-go-handler.md`](learning-journal/2026-08-26-http-network-go-handler.md)：从 HTTP Request、404/405、认证授权，一路连接 DNS、TCP/TLS、Nginx、Socket、Go `net/http`、`http.Handler` 与 `HandlerFunc`。

完整记录规则见 [`learning-journal/README.md`](learning-journal/README.md)。

---

## 什么内容应该放哪里

```text
一个稳定术语的短定义
→ glossary

多个概念之间的关系
→ knowledge-map / cheatsheet

某次学习纠正了一个长期误区
→ learning-journal

已经能独立教学的完整主题
→ lessons

只有亲手制造失败才能真正理解
→ exercises
```

不要为了目录看起来丰富，把同一个知识复制到四个文件。

---

## 什么不要长期保存

- 临时产品 UI 的点击路径；
- 一次机器/网络抖动；
- 整段聊天原文；
- 无证据猜测；
- 真实公司/客户/账号/Token 信息；
- 自己还没理解的大段 AI 输出。

这类内容会让知识库越来越大，却越来越难用。

---

## 换电脑回来时的推荐顺序

如果几周没看后端：

```text
1. knowledge-map
2. 当前主题 cheatsheet / glossary
3. 最近相关 learning journal
4. 对应 lesson
5. 需要时运行 exercise
```

目标不是恢复“读到第几章”，而是恢复当时已经建立的心智模型。
