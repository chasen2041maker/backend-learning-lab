# 后续扩展主题：什么时候值得再学

这份文件不是“缺失知识清单”。

它解决的问题是：

> 后端技术太多，我应该什么时候引入下一类复杂度，而不是看到名字就学？

原则：**由真实需求、故障和职责驱动。**

---

## 现在的核心主干

这些属于通用后端基本功，应该随着真实问题不断加深：

- HTTP / API contract / middleware；
- Authentication / Authorization / tenant / owner；
- Go `net/http`、`context`、goroutine/channel/error handling；
- Python FastAPI / asyncio（在 Agent/RAG 和已有练习中使用）；
- PostgreSQL、constraint、index、transaction、migration；
- idempotency、concurrency、timeout、retry、backpressure；
- Redis cache/session/rate-limit/Streams 的角色边界；
- Outbox、consumer idempotency、lease/fencing；
- unit/integration/contract/fault testing；
- logs/metrics/traces/SLO；
- Docker image / CI / deployment；
- Agent tool authorization、RAG permissions、budget、eval。

这些不是要求一次全部学完，而是在工作/项目遇到相应问题时回到对应 lesson。

---

# 第一批扩展：出现明确业务需求就学

## Object Storage / 大文件上传

当出现：

```text
图片 / PDF / 视频 / 大模型文件
```

再系统学习：

- S3/Object Storage；
- multipart upload；
- presigned URL；
- upload size limit；
- MIME/type validation；
- malware scanning；
- orphan cleanup；
- lifecycle / retention。

如果系统只有几 KB JSON，不需要提前深入。

---

## Full-text Search / OpenSearch

当 PostgreSQL 的普通过滤/全文搜索已经不能满足：

- 大规模相关性排序；
- 复杂全文检索；
- 独立搜索扩缩；
- 搜索分析；

再学习：

- inverted index；
- analyzer/tokenizer；
- OpenSearch/Elasticsearch；
- index mapping；
- refresh；
- event-driven projection；
- reindex；
- ACL filtering。

搜索索引通常是派生数据，不要忘记 source of truth 和重建路径。

---

## Object/Data Lifecycle

当开始保存真实长期数据时学习：

- retention；
- archival；
- privacy deletion；
- audit log；
- backup / restore；
- RPO / RTO；
- legal/compliance boundary。

“数据库有 Volume”并不等于完成这部分。

---

## Performance Profiling / Load Test

当感觉服务“慢”，不要立刻扩机器。

学习：

- CPU profile；
- heap profile；
- goroutine profile；
- Python profiling；
- load generation；
- saturation point；
- connection pool；
- queueing / Little's Law；
- flame graph。

目标是先证明瓶颈在哪里。

---

## Feature Flag / Canary / Progressive Delivery

当发布风险变大、有真实用户时，再深入：

- feature flag lifecycle；
- gradual rollout；
- canary；
- percentage/user/tenant targeting；
- metric-based rollback；
- flag cleanup。

Feature Flag 不是永久 if/else 配置垃圾场。

---

# 第二批扩展：单机/单数据库开始出现明确边界时

## PgBouncer / PostgreSQL Connection Architecture

当实例变多、连接数成为瓶颈时学习：

- session/transaction pooling；
- prepared statements 限制；
- max connections；
- pool sizing；
- failover behavior。

不要在只有一个开发 API 时为了“企业级”先加 PgBouncer。

---

## PostgreSQL Partitioning

当单表数据量、维护、时间范围查询已经出现真实问题时学习：

- range/list/hash partition；
- partition pruning；
- index/constraint；
- retention by partition；
- migration strategy。

Partition 不是自动性能按钮。

---

## Read Replica

当读压力明显且某些读允许 stale 时学习：

- replication lag；
- read routing；
- read-after-write；
- failover；
- replica health。

---

## Schema Registry / Event Compatibility

当事件消费者变多、独立部署后学习：

- schema version；
- backward/forward compatibility；
- Protobuf/Avro/JSON Schema；
- consumer-driven compatibility；
- replay old event。

只有一个进程一个 consumer 时无需为了形式先建平台。

---

# 第三批扩展：吞吐、保留或组织边界真实超出当前方案时

## Kafka / Redpanda

当 Redis Streams / PostgreSQL jobs/outbox 的边界已经被量化证明不够，例如：

- 很高持续吞吐；
- 长时间事件保留；
- 大量独立 consumer groups；
- 大规模 replay；
- partitioned ordered log 是核心需求；

再深入：

- partition；
- offset；
- consumer group；
- rebalance；
- retention；
- replication；
- producer idempotence；
- delivery semantics；
- schema evolution。

不要因为“异步系统就应该 Kafka”而引入。

---

## ClickHouse / OLAP

当真正出现：

```text
大量分析查询
高吞吐 append
按列聚合
```

并且 PostgreSQL analytics 已成为明确瓶颈时学习。

不要拿 ClickHouse 代替普通 OLTP 业务库。

---

## Database Sharding

只有单集群数据库真正达到容量/吞吐/隔离边界时再学：

- shard key；
- routing；
- hot shard；
- rebalance；
- cross-shard query；
- distributed transaction；
- global ID。

这是非常昂贵的复杂度，不是“大数据”三个字自动触发。

---

# 平台和基础设施深水区

## OpenTelemetry Collector / Telemetry Pipeline

当多个服务已经需要统一 telemetry 后再深入：

- OTLP；
- collector pipeline；
- processors/exporters；
- sampling；
- baggage；
- tail sampling；
- cost/cardinality control。

单服务阶段先学 signal 语义比先搭 Collector 更重要。

---

## Infrastructure as Code

当基础设施需要重复环境和审计时：

- Terraform / OpenTofu 等；
- desired state；
- state file；
- plan/apply；
- module；
- drift；
- secret boundary。

---

## Kubernetes 深度运维

只有职责真的涉及集群平台时深入：

- scheduler；
- CNI；
- CSI；
- autoscaler；
- admission；
- CRD/Operator；
- etcd；
- network policy；
- multi-tenant cluster；
- control plane failure。

普通后端工程师先做到“能读懂部署清单和诊断应用级问题”通常更有价值。

---

## Service Mesh

当服务数量、mTLS、traffic policy、telemetry 需求真正达到平台级复杂度时再看。

不要为了“微服务标准架构”先加一层 sidecar/mesh。

---

# 多区域与复杂一致性

出现明确全球低延迟、区域故障容忍或法规要求后，再深入：

- active-passive / active-active；
- global routing；
- replication conflict；
- quorum；
- consensus；
- multi-region database；
- failover/failback；
- data residency。

这部分需要先有扎实的 transaction、replication、failure model 基础。

---

# Agent / AI 进一步扩展

当普通 Agent 后端边界已经掌握后，再深入：

- distributed task orchestration；
- sandboxed code execution；
- tool marketplace / capability discovery；
- model routing；
- prompt/version management；
- evaluation platform；
- synthetic test generation；
- human-in-the-loop queue；
- memory lifecycle / privacy；
- multi-agent coordination。

始终先问：

```text
这项 Agent 能力解决的是模型问题，还是普通后端问题？
```

很多所谓 Agent 平台问题，本质仍然是：

```text
job state
permissions
idempotency
queue
budget
observability
```

---

# 判断“现在该不该学”的五问

每看到一个新技术，用下面五问过滤：

1. **现在有什么具体问题？**
2. **当前简单方案为什么不够？有数据/故障证据吗？**
3. **新技术解决哪一个明确瓶颈？**
4. **它会新增哪些失败、状态和运维成本？**
5. **如果三个月不用它，我会损失什么实际能力？**

如果只有：

```text
“听说这个企业都用”
```

就先放到这里，不进入主路线。
