# 后续扩展知识：什么时候再学

主路线完成前，不要同时展开所有主题。

## P0：当前工作最相关

- PostgreSQL migration、连接池、慢查询和恢复；
- Redis Streams、Outbox、幂等、重试、DLQ、租约；
- Go `net/http`、context、goroutine、错误处理和测试；
- Python asyncio、FastAPI、任务状态机和pytest；
- HTTP/gRPC/事件契约；
- Docker、K8s清单阅读、CI/CD和可观测性；
- Agent工具、预算、评测、事实来源和故障降级。

## P1：主路线后补充

- 对象存储、分片上传、预签名URL和病毒扫描；
- 全文搜索、OpenSearch索引与事件投影；
- PostgreSQL分区、只读副本、PgBouncer；
- 性能分析、压测、连接池和背压；
- Feature Flag、灰度、Canary和回滚；
- 数据保留、备份恢复、隐私删除和审计；
- 消息归档、重放工具和Schema Registry；
- S3/云服务基础与IaC概念。

## P2：出现真实瓶颈再学

- Kafka/Redpanda；
- ClickHouse；
- OpenTelemetry Collector深度配置；
- Service Mesh；
- 多区域容灾和复杂一致性协议；
- Kubernetes集群运维和Operator开发。

学习顺序由当前故障和职责驱动。能用PostgreSQL唯一约束解决的问题，不要先引入分布式锁；没有吞吐和保留证据时，不要因为架构图好看就引入Kafka。
