# Go `net/http` 工单练习

这个练习与 Python API 表达同一个领域，但使用 Go 标准库。目标是看懂 Go 服务的真实结构，而不是先学习大型 Web 框架。

## 运行

```powershell
go test ./...
go run ./cmd/server
```

服务监听 `http://127.0.0.1:8080`：

- `POST /api/v1/tickets`
- `GET /api/v1/tickets/{id}?tenant_id=tenant_demo`
- `POST /api/v1/tickets/{id}/close`
- `GET /health`

## 独立练习

1. 新增 `priority` 并验证允许值；
2. 为查询接口增加错误租户测试；
3. 为 close 增加一个并发版本冲突测试；
4. 增加列表和游标分页；
5. 使用 `context.WithTimeout` 模拟 Repository 超时。
