# Python FastAPI 工单练习

这是课程前半段的可运行服务。它故意使用内存 Repository，让你先掌握 HTTP、分层、状态机、错误和测试；第 5 周以后再把 Repository 替换为 PostgreSQL。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r ..\..\requirements-repo.lock
python -m pip install --no-deps -e .
pytest
uvicorn app.main:app --reload --port 8000
```

打开 `http://127.0.0.1:8000/docs`。

除 `/health` 外，示例请求使用本地教学凭据：

```http
Authorization: Bearer lab-token-tenant-a
```

租户来自服务端验证后的身份，不能通过 Body 或 Query 指定。固定 Token 只用于本地理解可信边界，不能用于真实系统。

## 已实现

- `POST /api/v1/tickets`：创建工单；
- `GET /api/v1/tickets/{ticket_id}`：查询；
- `GET /api/v1/tickets?limit=20`：当前身份租户的列表；
- `POST /api/v1/tickets/{ticket_id}/close`：乐观版本关闭；
- 统一错误响应、request ID、分层和异步测试。

## 独立练习

1. 新增 `priority=low|normal|high`；
2. 新增 reopen，但只允许 `closed → open`；
3. 为列表增加 `(created_at, id)` 游标分页；
4. 为重复关闭、跨租户读取和版本冲突补测试；
5. 把内存 Repository 换成 PostgreSQL，API/Service 测试不应大改。

不要直接让 AI 完成。先写契约、失败场景和测试。
