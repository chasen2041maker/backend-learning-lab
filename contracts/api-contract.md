# HTTP API 契约（学习版）

Base URL：`http://localhost:8000`（Python）或 `http://localhost:8080`（Go）。

## 通用响应

```json
{
  "code": "ok",
  "message": "ok",
  "request_id": "req_demo_001",
  "data": {}
}
```

`code` 是稳定机器错误码，`message` 用于人类阅读，不应让客户端解析 message 判断业务。

## 创建工单

```http
POST /api/v1/tickets
Content-Type: application/json
X-Request-ID: req_demo_001
Idempotency-Key: create-demo-001
```

```json
{
  "tenant_id": "tenant_demo",
  "title": "Cannot sign in"
}
```

成功：`201`。输入错误：`400/422`。完整项目必须实现 `Idempotency-Key`；早期内存练习暂未实现，留到事务章节。

## 查询工单

```http
GET /api/v1/tickets/{ticket_id}?tenant_id=tenant_demo
```

成功：`200`。不存在或跨租户：`404 ticket_not_found`。跨租户也返回 404，避免泄露资源存在性。

## 列表

```http
GET /api/v1/tickets?tenant_id=tenant_demo&limit=20&after=<cursor>
```

最终版本使用 `(created_at, id)` 编码的游标。早期练习允许先不分页。

## 关闭工单

```http
POST /api/v1/tickets/{ticket_id}/close
Content-Type: application/json
```

```json
{
  "tenant_id": "tenant_demo",
  "expected_version": 1
}
```

版本或状态冲突：`409`。重复请求是否返回原结果，需要在实现幂等键前明确约定。

## 稳定错误码

| HTTP | code | 含义 |
| --- | --- | --- |
| 400/422 | `invalid_ticket_input` | 输入非法 |
| 404 | `ticket_not_found` | 不存在或不可见 |
| 409 | `ticket_state_conflict` | 状态不允许 |
| 409 | `ticket_version_conflict` | 乐观版本冲突 |
| 429 | `rate_limited` | 限流 |
| 500 | `internal_error` | 未预期错误 |
| 503 | `dependency_unavailable` | 依赖暂不可用 |
