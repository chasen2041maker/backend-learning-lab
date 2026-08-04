# HTTP API 契约（v1）

Python 与 Go 必须通过同一份机器可读用例：[http-cases.json](http-cases.json)。任何字段、状态码或错误码变更，都先修改契约和共享用例，再修改两个实现。

## 身份与租户边界

除 `/health` 外，请求必须携带 `Authorization: Bearer <token>`。当前仓库只提供两个固定本地教学 Token：

- `lab-token-tenant-a` → `tenant_a`
- `lab-token-tenant-b` → `tenant_b`

它们不是生产认证方案。生产服务必须验证签名或 opaque credential，再由服务端生成 `Principal(subject, tenant_id)`。客户端不得在 Body、Query 或 Path 中指定 `tenant_id`；出现该字段按未知字段拒绝。跨租户读取统一返回 404，避免泄露资源是否存在。

## 通用响应

```json
{
  "code": "ok",
  "message": "ok",
  "request_id": "req_demo_001",
  "data": {}
}
```

`code` 是稳定机器码；客户端不得解析 `message` 判断业务。所有成功和错误响应均返回相同的 `X-Request-ID` Header 与 `request_id` 字段。

## 请求规则

- JSON 必须是单个完整对象；语法错误或尾随第二个 JSON 返回 `400 invalid_json`。
- 未知字段返回 `422 invalid_ticket_input`。
- `title` 去除首尾空白后长度为 1～200 个 Unicode code point，不按 UTF-8 字节数计算。
- 工单 ID 使用 RFC 4122 UUID v4 字符串。
- 列表 `limit` 默认为 20，范围 1～100。

## 端点

```http
POST /api/v1/tickets
Authorization: Bearer lab-token-tenant-a
Content-Type: application/json

{"title":"Cannot sign in"}
```

成功：`201`。

```http
GET /api/v1/tickets/{ticket_id}
GET /api/v1/tickets?limit=20
```

成功：`200`；不存在或不属于当前身份租户：`404 ticket_not_found`。

```http
POST /api/v1/tickets/{ticket_id}/close
Authorization: Bearer lab-token-tenant-a
Content-Type: application/json

{"expected_version":1}
```

版本或状态冲突：`409`。

## 稳定错误码

| HTTP | code | 含义 |
| --- | --- | --- |
| 400 | `invalid_json` | JSON 语法错误或包含尾随值 |
| 401 | `authentication_required` | 缺少或无效凭据 |
| 422 | `invalid_ticket_input` | 已解析 JSON 不满足字段/业务约束 |
| 404 | `ticket_not_found` | 不存在或当前租户不可见 |
| 409 | `ticket_state_conflict` | 状态不允许 |
| 409 | `ticket_version_conflict` | 乐观版本冲突 |
| 429 | `rate_limited` | 限流 |
| 500 | `internal_error` | 未预期错误 |
| 503 | `dependency_unavailable` | 依赖暂不可用 |
