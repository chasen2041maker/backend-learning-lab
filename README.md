# 后端工程学习实验室

这是一个面向后端初学者的可运行学习仓库。它不是“后端名词大全”，而是一条从 HTTP 请求开始，逐步走到数据库、Redis、异步事件、可靠性、容器和 AI 服务生产化的实践路线。

这个仓库同时承担**长期知识沉淀**的角色：平时可以通过对话、代码审查和真实问题学习；真正讲通、值得以后复习的内容再整理进 `lessons/`、`notes/` 和 `notes/learning-journal/`，而不是把聊天原文全部堆进仓库。

Python 主线、Go 延后 1～2 个阶段复现：

- Python 用 FastAPI 练习 AI/Agent 服务常见的 API、异步任务和测试；
- Go 用标准库 `net/http` 练习 BFF、微服务边界、并发和错误处理；
- PostgreSQL 保存业务事实；
- Redis 用于缓存、限流和事件流，但不充当唯一业务事实源；
- 综合项目是一套原创的“可靠工单 + Agent 任务后端”，不包含任何公司代码或内部信息。

## 从这里开始

1. 阅读 [学习方式与第一天](lessons/00-start-here.md)。
2. 按 [Windows 环境准备](lessons/00b-environment-setup.md) 检查 Python、Go、Git 和 Docker。
3. 打开 [学习路线](LEARNING_ROADMAP.md)，把它当作知识顺序和能力地图，不必机械追赶周数。
4. 从[第 1 课](lessons/01-request-lifecycle.md)启动 Python 服务，每学一小节就完成对应实验；Go 到第 8 周再开始。
5. 完成练习后，在 [学习进度表](progress/README.md) 写下“我能独立解释什么”。
6. 日常讨论中真正讲通的新知识，整理到 [对话学习日志](notes/learning-journal/README.md)，成熟后再并入正式课程或速查页。
7. 遇到问题或需要送审时，使用 [GPT 提问与整仓送审指南](HOW_TO_ASK_GPT.md)。

## 仓库结构

```text
backend-learning-lab/
├─ lessons/                     # 按顺序阅读的通俗教程
├─ exercises/
│  ├─ python-ticket-api/        # FastAPI 分层 API 与 pytest
│  ├─ go-ticket-api/            # Go net/http 分层 API 与 go test
│  ├─ sql-postgres/             # 表、索引、事务和查询练习
│  ├─ redis-lab/                # 缓存、幂等和 Streams 小实验
│  ├─ reliability-labs/         # 并发/鉴权/Webhook/Outbox/指标/RAG 微实验
│  └─ infrastructure/           # 本地 PostgreSQL + Redis
├─ contracts/                   # HTTP 与事件契约
├─ projects/reliable-support-agent/
│                                # 综合项目要求、里程碑和验收
├─ notes/
│  ├─ knowledge-map.md          # 后端知识地图
│  ├─ glossary.md               # 术语表
│  ├─ *-cheatsheet.md           # 高频专题速查
│  └─ learning-journal/         # 对话/审查中讲通的长期学习记录
├─ progress/                    # 打卡与 Debug 记录
├─ .github/workflows/ci.yml     # 公开仓库的最小 CI
└─ HOW_TO_ASK_GPT.md            # 提问、讲解和代码审查模板
```

## 知识应该放到哪里

为了避免仓库越维护越像聊天记录，新增内容按下面规则归档：

- `lessons/`：已经形成完整因果链、适合系统学习的成熟知识；
- `notes/learning-journal/`：某次讨论、调试或代码审查中真正讲通的关键点、误区和失败场景；
- `notes/*-cheatsheet.md`：隔几周回来时需要快速恢复记忆的专题；
- `notes/glossary.md`：需要一两句话快速定位含义的术语；
- `exercises/`：仅靠阅读不够、必须亲手制造失败和验证不变量的知识。

同一知识可以从 learning journal 开始，之后逐步提炼到 lesson、cheatsheet 或 exercise；不要为了“记录”而复制整段聊天。

## 学完应该能做到什么

你不需要背下所有 API，但应该能够：

1. 画出一次请求从客户端到当前服务响应的真实路径，并随课程逐步加入数据库等组件；
2. 分清 Handler、Service、Repository 和 Domain 的职责；
3. 写出带验证、错误码、分页和测试的 Python/Go API；
4. 解释索引、事务、隔离级别、锁和数据库 owner；
5. 设计幂等 Webhook，分析“落库后宕机”等失败窗口；
6. 解释缓存穿透、TTL、Redis Streams、Pending、ACK 和 DLQ；
7. 为超时、重试、取消、并发和任务租约选择合理方案；
8. 通过日志、指标、Trace 和测试定位问题；
9. 使用 Docker Compose 运行依赖，读懂基本 K8s 与 CI/CD 清单；
10. 把已经熟悉的 RAG 封装成可限流、可评测、可降级的生产服务。

## 每天推荐节奏

```text
10 分钟：关闭 AI，复述昨天的数据流
20 分钟：阅读当前小节
40 分钟：亲手写代码、运行测试、制造一个失败
15 分钟：记录根因、修复和验证证据
5 分钟：写下明天要从空白重做的一小段
```

工作交付仍然可以使用 AI，但学习练习必须先独立尝试。能运行不等于掌握；能解释失败窗口、独立修改并通过测试，才算掌握。

## 快速验证

Python：

```powershell
cd exercises\python-ticket-api
python -m pip install -r ..\..\requirements-repo.lock
python -m pip install --no-deps -e .
python -m pytest
```

这些命令直接使用当前 PATH 中的 Python 环境，不要求虚拟环境。先确认
`python --version` 为 3.11+，并始终使用 `python -m pip` 安装到同一个解释器。

Go：

```powershell
cd exercises\go-ticket-api
go test ./...
go run ./cmd/server
```

基础设施到第 5 周再启动，不要第一天同时安装和调试全部组件。整仓检查可在根目录运行 `powershell -File scripts/check.ps1`；脚本会显式检查 Git、Python、Go 和 Docker 的退出码，失败时不会输出“全部通过”。
