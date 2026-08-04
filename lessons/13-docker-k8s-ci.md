# 第 13 课：Docker、Kubernetes 与 CI/CD

## Docker 心智模型

- Image：只读的应用模板；
- Container：Image 的运行实例；
- Volume：独立于容器生命周期的数据；
- Network：容器之间的连接边界；
- Registry：保存 Image；
- Digest：镜像内容的不可变身份。

容器删除不等于 Volume 删除。数据库必须有明确的持久化、备份和恢复方案。

## Compose

本仓库 Compose 只启动本地 PostgreSQL 和 Redis。应用可先在宿主机运行，方便调试；掌握后再为应用编写 Dockerfile。

## Kubernetes 核心对象

- Deployment：声明副本和滚动更新；
- Service：为 Pod 提供稳定网络入口；
- ConfigMap：非秘密配置；
- Secret：秘密配置，但仍需访问控制和加密；
- Job：一次性任务，例如数据库迁移；
- HPA：基于指标扩缩容；
- Ingress/Gateway：集群入口。

## 发布身份

生产镜像应固定到 digest，而不是 `latest`。健康检查成功只证明探针通过，不自动证明业务、数据质量和真实供应商都已验收。

## Migration

数据库迁移通常由独立 Job 执行。应用发布要考虑：

- 新旧版本同时运行时的 schema 兼容；
- 大表修改和锁；
- 回滚是否会破坏新数据；
- migration ledger/checksum；
- 失败时停止发布。

## CI/CD 最小流程

```text
format → lint → unit test → contract/integration test
→ build → vulnerability scan → deploy → smoke → rollback check
```

## 练习

启动 Compose，查看健康状态和日志；停止并重启，验证 PostgreSQL 数据仍存在；再解释为什么这仍不等于具备生产数据库运维能力。
