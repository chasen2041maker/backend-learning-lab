# 后端知识地图

遇到一个功能时，按下面顺序检查，而不是先搜索框架代码：

```text
需求与边界
├─ 协议：HTTP / gRPC / Event / SSE
├─ 身份
│  ├─ Authentication：你是谁？
│  ├─ Principal：可信身份从哪里来？
│  ├─ Authorization：你能做什么？
│  └─ owner / tenant：资源到底属于谁？
├─ 凭证与会话
│  ├─ Cookie / Session / Session ID
│  ├─ Bearer / opaque token / JWT
│  ├─ Access Token / Refresh Token
│  └─ TTL / revoke / rotation / key rotation
├─ 领域：状态机 / 不变量 / 幂等语义
├─ 数据：schema / 约束 / 索引 / 事务 / migration
├─ 并发：锁 / version / deadline / cancel / lease
├─ 异步：Outbox / delivery / ACK / retry / DLQ
├─ 缓存：TTL / 一致性 / 重建 / 热点
├─ 安全
│  ├─ password hashing / Secret / HTTPS
│  ├─ XSS / CSRF / CORS
│  ├─ 注入 / SSRF / mass assignment
│  └─ 最小权限 / 审计 / 日志脱敏
├─ 观测：log / metric / trace / SLO
├─ 测试：unit / integration / contract / E2E / fault
└─ 运行：Docker / K8s / CI/CD / rollback / recovery
```

Agent/RAG 不是独立于这些主题的“特殊后端”。它额外增加模型非确定性、Token/成本预算、工具权限、事实来源和效果评测，但仍然需要上述全部基础。

尤其注意：**模型选择了一个 Tool，不代表 Tool 自动获得执行权限。**有副作用操作仍然必须经过服务端 Authentication、Authorization、tenant/owner 校验、必要的人机确认、幂等与审计。
