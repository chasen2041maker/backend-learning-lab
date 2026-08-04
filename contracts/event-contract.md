# 事件契约（v1）

机器校验规则见 [event.schema.json](event.schema.json)。Producer 在写入 Stream 前构造完整 Envelope；Consumer 先校验 Envelope，再执行业务副作用。

```json
{
  "event_id": "3d5157f1-701f-4e4f-a817-73b3944a5c35",
  "event_type": "ticket.closed",
  "event_version": 1,
  "occurred_at": "2026-08-04T10:00:00Z",
  "tenant_id": "tenant_demo",
  "request_id": "req_demo_001",
  "trace_id": "trace_demo_001",
  "payload": {
    "ticket_id": "00000000-0000-4000-8000-000000000001",
    "status": "closed",
    "version": 2
  }
}
```

## 消费者约束

- 按 `event_id` 幂等；业务写入与 `processed_events` 必须处于同一 PostgreSQL 事务。
- 未知可选字段应忽略；未知 `event_version` 进入可观察失败/DLQ，不静默 ACK。
- 不假设全局严格有序；需要顺序时使用实体 `version`，拒绝旧版本覆盖。
- 业务持久化成功后再 ACK。ACK 前宕机会重复投递，因此副作用必须幂等。
- payload 不包含 Token、密钥或不必要的隐私信息。
- `request_id` 用于单次请求关联，`trace_id` 用于跨服务链路，二者不能互相替代。
