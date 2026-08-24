# 后端术语表

- **ACK**：消费者确认消息已经完成处理。
- **ACID**：数据库事务的原子性、一致性、隔离性、持久性。
- **BFF**：Backend For Frontend，为特定客户端提供入口和有限聚合。
- **Cache Aside**：应用先查缓存，未命中再查事实源并回填。
- **Consumer Group**：多个消费者协作处理同一 Stream。
- **Cursor Pagination**：使用稳定排序键作为下一页位置。
- **Deadline**：一个操作最晚必须结束的绝对时间边界。
- **DLQ**：无法正常处理的消息隔离区，需要告警、诊断和重放流程。
- **Fencing Token**：单调版本，阻止过期 Worker/锁持有者写入。
- **Idempotency**：同一个操作重复执行，外部业务结果保持一致。
- **Lease**：有过期时间的任务所有权，允许故障接管。
- **Liveness**：进程是否需要重启。
- **N+1**：一次列表查询后对每行再查询一次导致大量请求。
- **Optimistic Lock**：通过 version 条件检测并发冲突。
- **Outbox**：把业务变更和待发布事件写进同一数据库事务。
- **Owner Service**：某类业务事实唯一允许写入的服务。
- **Pending**：Redis Streams 已投递但未 ACK 的消息。
- **Pessimistic Lock**：读取时锁定行，阻塞其他竞争事务。
- **Readiness**：实例是否应该接收新流量。
- **Request ID**：一次入口请求的关联标识。
- **SLO**：面向用户体验的服务目标。
- **SSRF**：服务端被诱导访问攻击者指定的内部/敏感地址。
- **Trace ID**：跨服务调用链的关联标识。
- **Transactional Outbox**：用本地数据库事务解决业务写入和消息发布双写。
- **TTL**：Key/数据的过期时间。

## 认证与安全

- **Authentication**：认证，回答“你是谁”，成功后应产生服务端可信 Principal。
- **Authorization**：授权，回答“你能做什么”，通常检查 role、permission、owner、tenant 等。
- **Principal**：认证成功后由服务端建立的可信主体信息，不应由客户端 Body 自报。
- **Cookie**：浏览器按 Domain、Path、Secure、SameSite 等规则保存和自动携带少量 HTTP 数据的机制。
- **Session**：服务端维护的一份会话状态；客户端通常只持有 Session ID。
- **Session ID**：用于查找服务端 Session 的不透明标识。
- **Token**：认证或授权凭证的统称。
- **Bearer Token**：持有者凭证；拿到有效 Token 的一方通常即可使用，因此必须防止泄露与重放。
- **Opaque Token**：客户端无法从 Token 本身读出语义，服务端通常需要查状态才能解析身份/权限。
- **JWT**：JSON Web Token，一种 Token 格式；常见签名 JWT 的 Payload 可读，签名主要防篡改而非保密。
- **Claim**：JWT 等 Token 中关于主体、签发方、过期时间等声明。
- **Access Token**：调用 API 的短期凭证。
- **Refresh Token**：用于换取新 Access Token 的长期高价值凭证，通常应支持服务端撤销。
- **Refresh Token Rotation**：每次刷新都发新 Refresh Token，并使旧 Token 失效，以便发现重放。
- **RBAC**：Role-Based Access Control，基于角色授权。
- **ABAC**：Attribute-Based Access Control，基于用户、资源、环境等属性组合授权。
- **XSS**：恶意脚本进入受信任页面执行。
- **CSRF**：利用浏览器自动携带认证凭据，诱导用户发送攻击者希望的请求。
- **CORS**：浏览器跨源访问策略，不是 Authentication 或 Authorization。
- **Password Hashing**：使用 Argon2id、bcrypt、scrypt 等专用算法不可逆地验证密码，而不是保存明文或可逆密文。
