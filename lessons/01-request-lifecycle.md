# 第 1 课：一次后端请求经历了什么

## 最小链路

```text
客户端
  → HTTP 请求
  → Gateway/BFF
  → Ticket Service
  → PostgreSQL
  → Service 组装结果
  → HTTP 响应
  → 客户端
```

每个箭头都可能失败。网络可能超时、参数可能非法、服务可能宕机、数据库可能冲突，响应也可能在成功落库后丢失。

## HTTP 请求的组成

```http
POST /api/v1/tickets HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Request-ID: req_demo_001
Idempotency-Key: create-ticket-001

{"tenant_id":"tenant_demo","title":"无法登录"}
```

- 方法和路径表达意图；
- Header 放协议元数据；
- Body 放业务输入；
- Request ID 用于关联日志；
- Idempotency Key 用于识别同一个操作的重试。

## HTTP 状态码与业务错误码

状态码描述 HTTP 层结果，业务错误码提供稳定的程序判断：

```json
{
  "code": "ticket_not_found",
  "message": "ticket does not exist",
  "request_id": "req_demo_001",
  "data": null
}
```

- `400`：输入格式错误；
- `401`：身份无效；
- `403`：身份有效但无权限；
- `404`：资源不存在；
- `409`：版本、幂等或状态冲突；
- `500`：未预期的服务错误；
- `503`：依赖暂时不可用。

## 三种容易混淆的超时

1. 客户端等待 BFF 超时；
2. BFF 调用下游服务超时；
3. 服务查询数据库超时。

上游超时不代表下游一定失败。服务可能已经落库，只是响应没有送达，所以写操作的重试必须配合幂等。

## 练习

画出“创建工单”链路，并回答：

- 数据库提交成功后，服务返回响应前宕机会怎样？
- 客户端收到超时后重新发送，会不会创建两个工单？
- 只打印“发生错误”为什么无法排查？
