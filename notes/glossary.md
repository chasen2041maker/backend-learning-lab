# 后端术语表

这个文件只做**快速定位**：每个词尽量用一两句话说明。需要完整因果链时去对应 `lessons/`，不要把术语表当教程背。

---

## HTTP、进程与 API

- **Process（进程）**：正在运行的程序实例，拥有自己的内存和操作系统资源。源代码文件本身不是进程。
- **Port（端口）**：主机上用于区分网络服务的数字标识；`127.0.0.1:8081` 表示本机 loopback 地址上的 8081 端口。
- **Handler**：接收具体 HTTP 请求并构造响应的入口，通常负责协议层解析、验证和错误映射。
- **Middleware**：在请求到达最终 Handler 前后执行的公共逻辑，例如 request ID、日志、认证、限流。
- **Router**：根据 Method/Path 等把请求分发到对应 Handler。
- **Request ID**：一次入口请求的关联标识，便于把同一次请求的日志串起来。
- **HTTP 400**：请求语法/格式无法被接受；具体 400/422 边界取决于 API 契约。
- **HTTP 401**：缺少有效认证身份，例如 Token 缺失、无效或过期。
- **HTTP 403**：身份已经确认，但没有当前操作所需权限。
- **HTTP 404**：资源不存在；某些多租户系统也故意用它隐藏其他租户资源是否存在。
- **HTTP 409**：常用于资源状态/并发冲突；具体使用要由契约定义。
- **REST**：围绕 HTTP/资源语义设计 API 的架构风格；现实中常泛指 HTTP + JSON 的资源型 API。
- **API Contract**：客户端和服务端共同依赖的外部行为，包括 Method、Path、Header、Body、状态码、错误码和兼容规则。

---

## 分层与业务

- **Service Layer**：负责用例和业务规则，不应被 HTTP/SQL 细节淹没。
- **Repository**：业务代码访问持久化事实的边界；不是单纯“把 SQL 移到另一个文件”。
- **Domain Invariant（业务不变量）**：系统任何合法状态都必须满足的规则，例如 closed 工单不能再次关闭。
- **State Machine（状态机）**：明确状态集合和允许的状态转换，避免任何代码随便写 status。
- **Owner / Fact Owner**：某类业务事实的权威写入边界；其他模块/服务不应绕过它直接改事实。
- **BFF**：Backend For Frontend，为某一类客户端提供适配和有限聚合的后端入口。
- **API Gateway**：位于外部客户端和内部 API 之间的入口，可承担路由、认证、限流、观测等横切职责。
- **Reverse Proxy（反向代理）**：代表后端服务器接收客户端流量并转发；可承担 TLS、路由等职责。
- **Load Balancer（负载均衡器）**：把流量分配给多个可用实例，避免客户端自己选择具体后端实例。

---

## Authentication、Session 与 Token

- **Authentication**：认证，回答“你是谁”，成功后应产生服务端可信 Principal。
- **Authorization**：授权，回答“你能做什么”，通常检查 role、permission、owner、tenant 等。
- **Principal**：认证成功后由服务端建立的可信主体信息，不应由客户端 Body 自报。
- **Cookie**：浏览器按 Domain、Path、Secure、SameSite 等规则保存并自动携带少量 HTTP 数据的机制。
- **Session**：服务端维护的一份会话状态；客户端通常只持有 Session ID。
- **Session ID**：用于定位服务端 Session 的不透明随机标识。
- **Token**：认证/授权凭证的统称，并不代表某一种固定格式。
- **Bearer Token**：持有者凭证；持有有效 Token 的一方通常即可使用，因此泄露后可被重放。
- **Opaque Token**：客户端无法从 Token 本身读出身份语义，服务端需要查状态或验证系统解析。
- **JWT**：JSON Web Token，一种 Token 格式；常见签名 JWT 的 Payload 可读，签名主要保护完整性/真实性而不是保密。
- **Claim**：Token 中关于 subject、issuer、audience、过期时间等声明。
- **Access Token**：调用 API 的短期凭证。
- **Refresh Token**：用于换取新 Access Token 的长期高价值凭证，通常需要服务端撤销能力。
- **Refresh Token Rotation**：每次刷新签发新的 Refresh Token 并使旧 Token 失效，用于降低重放风险。
- **RBAC**：Role-Based Access Control，基于角色分配权限。
- **ABAC**：Attribute-Based Access Control，基于用户、资源、环境等属性组合做授权判断。

---

## 密码与 Web 安全

- **Password Hashing**：使用 Argon2id、bcrypt、scrypt 等专用算法不可逆验证密码，不保存明文或可逆密码密文。
- **Salt**：每个密码 Hash 使用的随机值，使相同密码不会得到相同存储结果，并降低预计算攻击效果。
- **XSS**：Cross-Site Scripting，恶意脚本进入受信任页面并在用户浏览器中执行。
- **CSRF**：Cross-Site Request Forgery，利用浏览器自动携带 Cookie 等凭据诱导用户发出攻击者希望的请求。
- **CORS**：浏览器跨源读取策略，不是后端 Authentication/Authorization，也不是 API 防火墙。
- **SSRF**：Server-Side Request Forgery，服务端被诱导访问攻击者指定的内部或敏感地址。
- **SQL Injection**：把不可信输入拼进 SQL 结构导致查询语义被攻击者改变；参数化查询是核心防线之一。
- **Mass Assignment**：把客户端对象字段无差别映射到内部模型，导致 `role`、`tenant_id` 等不应修改字段被篡改。
- **Least Privilege（最小权限）**：用户、服务、数据库账号、容器只获得完成职责所需的最少权限。

---

## PostgreSQL、SQL 与数据

- **Primary Key**：表中每行的唯一身份约束。
- **Foreign Key**：保护引用关系，避免子记录指向不存在的父记录。
- **UNIQUE Constraint**：保证字段或字段组合不能出现重复事实，也是重要的并发正确性工具。
- **CHECK Constraint**：让数据库拒绝不满足条件的行，例如非法 status。
- **Index（索引）**：用于加速特定查询访问路径的数据结构，会增加写入和存储成本，应由真实查询模式驱动。
- **Composite Index（组合索引）**：由多列组成的索引，列顺序和真实 WHERE/ORDER BY 访问模式相关。
- **EXPLAIN**：查看 PostgreSQL 对 SQL 的执行计划，避免靠猜测判断是否走索引。
- **N+1**：先查询 N 条记录，再为每条单独查一次相关数据，导致大量数据库 round trip。
- **Cursor Pagination**：使用稳定排序键记录“下一页从哪里继续”，常用于避免大 OFFSET 和分页漂移。
- **Migration**：可追踪地演进数据库 schema 的变更步骤。
- **Connection Pool**：复用有限数量数据库/Redis 连接，避免每请求重复建立连接；pool 过大也会压垮下游。
- **Source of Truth**：某类数据的权威事实来源，其他 cache/index/projection 可以由它重建。

---

## Transaction、并发与幂等

- **ACID**：数据库事务的 Atomicity、Consistency、Isolation、Durability。
- **Transaction**：让一组数据库变化形成明确提交/回滚边界；不能自动回滚邮件、HTTP、Redis 等外部副作用。
- **COMMIT**：事务成为已提交事实的关键时刻；它和客户端收到 HTTP 成功响应不是同一个时刻。
- **Isolation Level**：定义并发事务可以看到哪些状态以及如何处理冲突。
- **Optimistic Lock**：通过 `version` 等条件检测数据在读取后是否被别人修改，冲突时拒绝旧更新。
- **Pessimistic Lock**：读取时先锁定目标数据，让竞争事务等待，例如 `SELECT ... FOR UPDATE`。
- **Deadlock**：多个事务相互等待对方持有的锁，数据库通常会终止其中一个来打破循环。
- **Race Condition**：结果依赖并发操作交错时序；可以发生在内存、数据库或分布式业务层。
- **Data Race**：多个执行单元并发访问同一内存位置且至少一个写、缺少正确同步的一类低层 race。
- **Lost Update**：两个并发更新基于旧状态写回，后一个覆盖前一个变化。
- **Idempotency**：同一个逻辑操作被重复执行时，外部业务副作用仍只发生一次或保持同一结果。
- **Idempotency Key**：客户端标识同一逻辑操作的键，服务端通常用持久唯一约束和请求摘要保护。

---

## Go / Python 并发

- **Concurrency（并发）**：多个任务在同一时间段内交错或重叠推进，不要求真的同时执行。
- **Parallelism（并行）**：多个任务在同一时刻由不同计算资源真正同时执行。
- **Goroutine**：由 Go runtime 管理和调度的轻量执行单元，是 Go 表达并发的核心机制之一。
- **Channel**：Go 中 goroutine 之间传递值和同步的一种机制。
- **Mutex**：保护共享临界区，一次只允许一个竞争执行者进入。
- **Worker Pool**：固定/受限数量 Worker 从任务队列取工作，用于限制并发而不是“任务多少就启动多少”。
- **Event Loop**：asyncio 等模型中调度 coroutine 的循环；等待非阻塞 I/O 时可运行其他任务。
- **Deadline**：一个操作最晚必须结束的绝对时间边界。
- **Timeout**：相对时长限制，例如“最多等待 2 秒”。
- **Cancellation**：通知下游工作已经不再需要；代码/依赖必须配合才能真正停止。
- **Backpressure**：当下游处理不过来时，让上游减速、等待、拒绝或有界排队，防止无限堆积。
- **Jitter**：在重试/TTL 时间上加入随机扰动，避免大量客户端同步重试或同时过期。

---

## Redis、缓存与协调

- **Redis**：通过网络访问的内存型数据服务器，可承担 cache、session、rate limit、coordination、Streams 等不同角色。
- **Cache Aside**：应用先查缓存，miss 后查事实源并回填；数据库通常仍是 source of truth。
- **TTL**：Key/数据的过期时间，不等于数据库和缓存的强一致保证。
- **Cache Penetration（穿透）**：大量查询不存在数据，每次 cache miss 后都打到事实库。
- **Cache Breakdown / Hot-key Expiry（击穿）**：热门 key 过期时大量请求同时回源。
- **Cache Avalanche（雪崩）**：大量 key 同时过期或缓存整体不可用，导致大规模回源。
- **Eviction**：Redis 达到内存上限时按策略提前淘汰 Key 或拒绝写入。
- **Lease**：有过期时间的临时所有权，Owner 失效后其他 Worker 可以接管。
- **Fencing Token**：单调递增版本，阻止旧 Worker/过期锁持有者在新 Owner 接管后继续写入。

---

## 异步、消息与可靠性

- **Job**：等待某个 Worker 执行的一项工作。
- **Command**：请求某个系统执行动作，例如 `CloseTicket`。
- **Event**：描述已经发生的事实，例如 `TicketClosed`。
- **ACK**：消费者确认一条消息已经完成处理。
- **At-least-once**：消息至少会投递一次，可能重复，因此消费者需要幂等。
- **Consumer Group**：多个消费者协作处理同一消息流的一组逻辑消费者。
- **Pending**：Redis Streams 等系统中已交给消费者但尚未 ACK 的消息。
- **Reclaim / Claim**：原消费者失效后，让其他消费者接管长期 Pending 消息。
- **Outbox / Transactional Outbox**：把业务变化和“待发布事件”写入同一个本地数据库事务，避免 DB + Broker 双写丢事件。
- **DLQ**：Dead Letter Queue，多次无法正常处理的消息隔离区；必须有诊断和重放流程，不是垃圾桶。
- **Backlog**：待处理任务/消息积压；oldest age 常比单纯数量更能说明系统是否跟得上。

---

## Testing、Debug 与 Observability

- **Unit Test**：验证小范围业务逻辑，不依赖真实外部系统。
- **Integration Test**：验证多个真实组件交互，例如真实 PostgreSQL schema/SQL/transaction。
- **Contract Test**：验证一个实现是否遵守共享外部协议/行为。
- **E2E Test**：从较真实入口串联多个组件验证关键用户路径。
- **Regression Test**：为已发生 bug 保留的可重复测试，防止相同问题回来。
- **Fault Test**：主动制造 timeout、崩溃、重复等失败窗口来证明恢复能力。
- **Log**：具体事件记录，适合回答“这一件事情发生了什么”。
- **Metric**：聚合时间序列信号，适合看请求率、错误率、延迟、资源趋势。
- **Trace**：一次调用跨组件/Span 的执行链，帮助定位端到端时间花在哪里。
- **Trace ID**：跨多个 Span/服务关联同一次分布式调用链的标识。
- **RED**：Rate、Errors、Duration，请求型服务最实用的基础指标组合之一。
- **Liveness**：进程是否已经坏到需要重启。
- **Readiness**：实例现在是否应该接收新流量。
- **SLI**：Service Level Indicator，实际测量的用户服务质量信号。
- **SLO**：Service Level Objective，对 SLI 设定的内部服务目标。
- **SLA**：Service Level Agreement，对外服务协议，可能带商业/赔偿责任。
- **Error Budget**：由 SLO 推导出的允许失败预算，用来平衡发布速度和可靠性。

---

## Docker、CI/CD 与 Kubernetes

- **Image**：只读、可版本化的应用运行模板和元数据。
- **Container**：从 Image 启动出的运行实例，通常共享宿主机 Kernel，而不是完整 Guest VM。
- **Volume**：生命周期可以独立于 Container 的持久数据存储；Volume 不是备份。
- **Registry**：存储和分发 Container Image 的服务。
- **Image Tag**：人类友好的镜像标签，可能被重新指向；不保证内容不可变。
- **Image Digest**：基于内容的不可变镜像身份，适合精确发布和回滚。
- **CI**：Continuous Integration，代码变化后自动运行集成前验证的工程流程。
- **Pipeline**：按顺序/依赖组织的一组自动化步骤；CI/CD 可以由 Pipeline 实现。
- **Continuous Delivery**：构建并验证到随时可发布，生产发布可能仍需人工批准。
- **Continuous Deployment**：满足自动验证后继续自动发布到生产的一类流程。
- **Pod**：Kubernetes 最小调度单位，可包含一个或多个共享网络/Volume 的 Container。
- **Deployment**：声明应用副本和滚动更新等期望状态的 Kubernetes 对象。
- **Kubernetes Service**：给动态 Pod 集合提供稳定网络访问入口；与代码的 Service Layer 不是同一概念。
- **ConfigMap**：Kubernetes 中保存非敏感配置的对象。
- **Kubernetes Secret**：Kubernetes 中保存敏感配置的对象，但仍需要 RBAC、加密和 Secret 管理边界。
- **HPA**：Horizontal Pod Autoscaler，根据指标调整 Pod 副本数量；不能替代下游容量规划。

---

## 分布式服务

- **Modular Monolith**：单一部署单元，但内部模块和事实 Owner 清楚的架构。
- **Microservice**：可独立部署/运行的服务边界，用网络复杂度换取独立演进、扩缩和组织 ownership 等能力。
- **Service Discovery**：让调用方通过稳定名称找到动态变化的服务实例。
- **gRPC**：常基于 HTTP/2 和 Protocol Buffers 的 RPC 框架；看起来像函数调用，实际上仍然有网络失败和 deadline。
- **Protobuf**：Protocol Buffers，结构化二进制 schema/序列化格式，字段编号需要兼容演进。
- **Eventual Consistency**：不同投影/服务短时间内允许看到不同状态，最终通过异步传播收敛；必须明确 source of truth 和允许延迟。
- **Saga**：跨多个独立事务边界的长业务流程，通过状态机和补偿等方式处理部分成功，不能被一个本地 transaction 自动回滚。

---

## RAG / Agent

- **RAG**：Retrieval-Augmented Generation，先从受控知识源检索相关内容，再把结果提供给模型生成答案。
- **Embedding**：把输入映射成向量表示，常用于语义检索；Embedding/向量索引通常是派生数据。
- **Vector Index / Vector DB**：支持向量近邻搜索的索引/存储系统，RAG 中通常不是业务事实的唯一 source of truth。
- **Workflow**：主要由程序确定控制流的多步骤执行过程。
- **Agent**：允许模型根据目标、状态和可用工具动态决定部分下一步动作的系统。
- **Tool / Function Calling**：模型输出结构化工具调用意图；真正的工具执行、权限、幂等仍由应用负责。
- **Tool Registry**：保存工具 schema、权限、side effect、timeout、成本、可用性等执行元数据的注册表。
- **Prompt Injection**：不可信输入/文档试图改变模型指令或诱导调用危险工具；不能只靠 Prompt 解决权限问题。
- **Grounding**：让模型输出中的事实能够被当前受信数据/来源支持。
- **Offline Eval**：用固定样本集重复比较 Retrieval/Model/Workflow 版本。
- **Bad Case**：失败样本；应按 retrieval、permission、prompt、tool、model、timeout 等根因分类，而不是统一“改 Prompt”。

---

如果某个术语仍然只能背定义，打开对应 lesson，把它放回真实请求、状态变化和失败场景中再理解。
