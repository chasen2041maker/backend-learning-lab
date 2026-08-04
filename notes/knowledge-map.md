# 后端知识地图

遇到一个功能时，按下面顺序检查，而不是先搜索框架代码：

```text
需求与边界
├─ 协议：HTTP / gRPC / Event / SSE
├─ 身份：认证 / 授权 / owner / tenant
├─ 领域：状态机 / 不变量 / 幂等语义
├─ 数据：schema / 约束 / 索引 / 事务 / migration
├─ 并发：锁 / version / deadline / cancel / lease
├─ 异步：Outbox / delivery / ACK / retry / DLQ
├─ 缓存：TTL / 一致性 / 重建 / 热点
├─ 安全：输入 / 注入 / SSRF / Secret / 审计
├─ 观测：log / metric / trace / SLO
├─ 测试：unit / integration / contract / E2E / fault
└─ 运行：Docker / K8s / CI/CD / rollback / recovery
```

Agent/RAG 不是独立于这些主题的“特殊后端”。它额外增加模型非确定性、Token/成本预算、工具权限、事实来源和效果评测，但仍然需要上述全部基础。
