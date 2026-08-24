# 后端工程学习知识库

这是一个用于**长期学习后端工程**的公开仓库。它不是固定课表，也不是“把所有后端名词塞进来”的百科全书。

主要学习方式是：

```text
和 AI / 代码 / 真实问题对话
        ↓
把一个概念真正讲通
        ↓
亲手运行、制造失败、验证边界
        ↓
把值得长期保留的知识整理进仓库
```

因此，这个仓库既是教程，也是跨电脑可访问的个人后端知识库和实验室。

## 新 AI / 新电脑：先从这里接棒

如果这是一个新的 ChatGPT / Codex / AI 会话，不要先从第 0 课重新讲，也不要看到高级文件就假设已经掌握。

按顺序读取：

1. **[`LEARNER_PROFILE.md`](LEARNER_PROFILE.md)**：这个学习者应该怎么教、哪些概念只是“见过”而不是掌握；
2. **[`progress/current-focus.md`](progress/current-focus.md)**：当前真正学到哪一段、下一步应该从哪里继续；
3. **[`GROWTH_PATH.md`](GROWTH_PATH.md)**：从后端新手到“10 年开发成熟度”的长期能力阶梯；
4. **[`LEARNING_ROADMAP.md`](LEARNING_ROADMAP.md)**：各后端知识之间的依赖关系；
5. 再进入当前主题对应的 lesson / journal / exercise。

当前进度文件永远只是接棒辅助。**最新对话中用户实际表现出来的理解程度优先。**

长期目标不是“十年后才算完成”，而是逐步获得成熟工程师常见的能力：

```text
需求分析
→ 最小正确设计
→ 数据/身份/事务边界
→ 并发/重复/失败推演
→ 测试与观测证据
→ 性能/可靠性/安全/成本权衡
→ 系统演进和复杂度控制
```

## 最重要的使用原则

1. **问题驱动，不按日历驱动。** `LEARNING_ROADMAP.md` 是知识依赖图，不是“20 周必须完成”的计划。
2. **概念优先于框架。** 先搞懂 HTTP、身份、事务、并发、失败窗口，再决定 Gin/FastAPI/Redis/K8s 怎么用。
3. **Go 和 Python 都是实现工具。** 当前重点学 Go 时，就用 Go 做主实现；Python 用于比较、Agent/RAG 和已有练习。不再规定“必须先 Python 后 Go”。
4. **能运行不等于掌握。** 至少要能解释输入、状态变化、输出、失败点和为什么这样设计。
5. **不为了架构图高级而加组件。** 能用单服务 + PostgreSQL 解决，就不要先拆微服务、加 Kafka、上 K8s。

## 仓库里的内容分别干什么

```text
backend-learning-lab/
├─ LEARNER_PROFILE.md            # 长期教学画像：新 AI 先读
├─ GROWTH_PATH.md                # 新手 -> 成熟高级工程师的能力阶梯
├─ lessons/                     # 已经整理成熟、可独立阅读的系统教程
├─ notes/
│  ├─ knowledge-map.md          # 后端知识之间的依赖和位置
│  ├─ glossary.md               # 快速查术语
│  ├─ *-cheatsheet.md           # 隔几周回来快速恢复记忆
│  └─ learning-journal/         # 对话/调试中真正讲通的知识记录
├─ exercises/                   # 必须亲手运行、失败、修复才能掌握的实验
├─ contracts/                   # HTTP / 事件的机器可执行契约
├─ projects/reliable-support-agent/
│                              # 把基础逐阶段整合起来的综合项目
├─ progress/
│  ├─ current-focus.md          # 当前教学接棒点
│  └─ ...                       # 能力证据和 Debug 记录
├─ scripts/                     # 仓库校验工具
└─ HOW_TO_ASK_GPT.md            # 对话学习、送审和知识沉淀的用法
```

## 应该从哪里看

如果你只是想继续正常学习，不需要从第 0 课顺序读到第 16 课。

先看 [`progress/current-focus.md`](progress/current-focus.md)，再问自己“我现在卡在哪一层”：

| 当前问题 | 去哪里 |
| --- | --- |
| HTTP 请求、端口、Handler、状态码 | `lessons/01-request-lifecycle.md` |
| Handler / Service / Repository 为什么分层 | `lessons/02-*`、`03-*` |
| API 输入、契约、可信 tenant | `lessons/04-api-contracts.md` |
| SQL、表、约束、索引、连接 | `lessons/05-sql-postgresql.md` |
| 事务、锁、重复请求、幂等 | `lessons/06-transactions-idempotency.md` |
| Redis、缓存、TTL、锁 | `lessons/07-redis.md` |
| goroutine、async、并发、timeout、context | `lessons/08-concurrency-timeouts.md` |
| 消息、Outbox、Streams、ACK、Pending | `lessons/09-streams-outbox.md` |
| Cookie、Session、JWT、权限、安全 | `lessons/10-auth-security.md` |
| 测试、代码审查、Debug | `lessons/11-testing-debugging.md` |
| 日志、指标、Trace、SLO | `lessons/12-observability.md` |
| Docker、镜像、CI、K8s | `lessons/13-docker-k8s-ci.md` |
| 网关、微服务、REST/gRPC/事件 | `lessons/14-grpc-events-boundaries.md` |
| RAG/Agent 怎么成为可靠后端服务 | `lessons/15-rag-agent-production.md` |
| 系统设计到底怎么推出来 | `lessons/16-system-design.md` |

完整依赖关系见 [学习路线](LEARNING_ROADMAP.md)、[成长路径](GROWTH_PATH.md) 和 [知识地图](notes/knowledge-map.md)。

## 对话学到的知识怎么沉淀

不是把聊天记录整段复制进来。

### 先进入 learning journal

当一次对话真正纠正了一个理解，例如：

```text
JWT ≠ Bearer Token
Bearer 说明凭证怎么使用
JWT 说明 Token 可以长什么样
Cookie 是浏览器机制
Session 是服务端会话状态
```

这种“之前容易混淆、现在已经讲通”的知识，可以整理进 `notes/learning-journal/`。

### 再决定要不要升级

- 能独立形成一整套教程 → `lessons/`
- 只需要一分钟快速恢复 → `*-cheatsheet.md`
- 只是一个术语 → `glossary.md`
- 只有亲手跑过才能理解 → `exercises/`

详见 [learning journal 规则](notes/learning-journal/README.md)。

### 约定触发词

对话中直接说：

```text
更新仓库
```

表示：

```text
检查最近真正新增的长期知识
→ 先读已有内容避免重复
→ 更新最合适的 lesson/journal/exercise/profile/current-focus
→ 推送远端
→ 验证 branch / compare / CI
```

不是把聊天全文保存。

## 学习时真正要追求的能力

不是“知道多少名词”，而是逐渐能做到：

```text
一个请求来了
↓
我知道它经过哪些层
↓
我知道哪些输入可信、哪些不可信
↓
我知道数据在哪里变化
↓
我知道事务能保护到哪里
↓
我知道并发/重试可能造成什么重复或覆盖
↓
我知道依赖挂掉以后系统怎么失败
↓
我知道用什么日志/测试/指标证明我的判断
```

最终你应该能够从一个需求推导设计，而不是从“我要不要用 Redis/Kafka/K8s”开始。

## Go / Python / SQL / Redis 怎么分工

### Go

适合当前后端基础训练：

- `net/http`；
- middleware；
- `context.Context`；
- error handling；
- goroutine/channel；
- 并发安全；
- 服务边界。

基础阶段优先标准库，避免框架替你隐藏 HTTP 细节。

### Python

主要用于：

- 已有 FastAPI 分层练习；
- asyncio 对比；
- RAG/Agent 服务；
- 快速可靠性微实验。

### PostgreSQL

保存业务事实，学习：

- schema；
- constraint；
- index；
- transaction；
- lock；
- migration；
- query plan。

### Redis

只在明确知道角色时使用：

- cache；
- session / 短期状态；
- rate limit；
- coordination；
- Streams。

不要把无法重建的核心业务事实只放 Redis。

## 综合项目怎么用

[可靠工单 + Agent 后端](projects/reliable-support-agent/README.md)不是要求一次完成的“大项目”。

正确演进顺序是：

```text
单服务 + 内存
↓
单服务 + PostgreSQL
↓
事务 / 鉴权 / 幂等
↓
Redis / 并发（确有理由时）
↓
Outbox / Worker / Streams
↓
Agent / RAG
↓
最后才考虑 Gateway、拆服务、K8s
```

每加一个组件，都必须能回答：

> 它解决了前一版的什么具体问题？不用它会发生什么？

## 如何判断“我会了”

用 [能力进度表](progress/README.md)，不要用“读完章节”判断。

建议四级：

```text
L1 见过：知道名词
L2 能解释：能画出数据流和失败点
L3 能独立：能自己实现、测试、排错
L4 能权衡：知道什么时候不用它，以及替代方案
```

仓库大多数基础知识至少追求 L2～L3。

## 环境与快速验证

Windows 环境见 [环境准备](lessons/00b-environment-setup.md)。

Go：

```powershell
cd exercises\go-ticket-api
go test ./...
go run ./cmd/server
```

Python：

```powershell
cd exercises\python-ticket-api
python -m pip install -r ..\..\requirements-repo.lock
python -m pip install --no-deps -e .
python -m pytest
```

整仓检查：

```powershell
powershell -File scripts/check.ps1
```

检查通过只说明当前自动化验证通过，不代表已经理解，也不代表达到生产级。

## 公开仓库安全边界

永远不要提交：

- 公司代码或架构；
- 内部 URL；
- 客户数据；
- 真实日志；
- 密码、Token、API Key；
- 私有 Prompt / Secret；
- 任何无法公开的数据。

`LEARNER_PROFILE.md` 也只保存适合公开的**技术学习上下文**，不保存私人身份、工作机密或生活信息。

只使用虚构业务和本地生成数据。

---

这个仓库的目标不是让目录越来越大，而是让你几个月后换一台电脑，或打开一个新的 AI 对话，仍然能快速恢复：**现在真正理解了什么、下一步该从哪里继续，以及最终要成长成怎样的后端工程师。**
