# 综合项目分阶段交付

综合项目不是“一周做完”的大作业。每个阶段都必须能单独运行、测试、回退；验收通过后打 Git Tag 保存证据。

## Phase 0：契约与内存纵切（约 1～2 周）

- Python 工单 API + Go Gateway 最小纵切；
- 可信测试身份、统一 Envelope、共享契约测试；
- 不接 PostgreSQL/Redis/真实模型。

完成证据：`git tag capstone-p0-memory`。

## Phase 1：PostgreSQL 事实源（约 2 周）

- migration、连接池/timeout、tenant-scoped Repository；
- 乐观锁、游标分页、幂等记录；
- PostgreSQL 集成测试与备份/恢复说明。

完成证据：`git tag capstone-p1-postgres`。

## Phase 2：Webhook + Outbox + Streams（约 2 周）

- 原始字节 HMAC、时间窗、去重/乱序；
- Outbox claim/lease/fencing/retry/DLQ；
- Pending reclaim、消费者幂等和故障演练。

完成证据：`git tag capstone-p2-async`。

## Phase 3：受控 Agent Task（约 2 周）

- 先接 deterministic Fake Provider，再考虑真实 Provider；
- tenant 文档权限、来源、deadline、Token/费用预算；
- 有副作用 Tool 的授权、确认、幂等、审计与补偿；
- task lease/fencing、取消和 SSE 重连。

完成证据：`git tag capstone-p3-agent`。

## Phase 4：观测、部署与送审（约 1～2 周）

- RED/Outbox/Stream/Agent 指标与告警；
- Compose、非 root 镜像、Probe、CI 和敏感信息扫描；
- 六个故障实验、架构一页纸、10 分钟独立讲解。

完成证据：`git tag capstone-p4-review-ready`。

Tag 是阶段快照，不代表线上发布。若某阶段没有可运行测试和失败恢复证据，不进入下一阶段。
