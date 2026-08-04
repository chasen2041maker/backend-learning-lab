# 事件契约（学习版）

## 公共 Envelope

```json
{
  "event_id": "evt_01J...",
  "event_type": "ticket.closed",
  "event_version": 1,
  "occurred_at": "2026-08-04T10:00:00Z",
  "tenant_id": "tenant_demo",
  "request_id": "req_demo_001",
  "trace_id": "trace_demo_001",
  "payload": {}
}
```

## `ticket.created` v1

```json
{
  "ticket_id": "00000000-0000-0000-0000-000000000001",
  "title": "Cannot sign in",
  "status": "open",
  "version": 1
}
```

## `ticket.closed` v1

```json
{
  "ticket_id": "00000000-0000-0000-0000-000000000001",
  "status": "closed",
  "version": 2
}
```

## 消费者约束

- 按 `event_id` 幂等；
- 未知可选字段应忽略；
- 未知事件版本进入可观察失败/DLQ，不静默 ACK；
- 不假设全局严格有序；需要顺序时使用实体版本并拒绝旧版本覆盖；
- 业务持久化成功后再 ACK；
- payload 不包含 Token、密钥或不必要的隐私信息。
