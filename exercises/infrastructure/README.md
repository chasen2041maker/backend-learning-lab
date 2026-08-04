# 本地 PostgreSQL 与 Redis

## 启动

```powershell
Copy-Item .env.example .env
docker compose up -d
docker compose ps
```

## 验证

```powershell
docker compose exec postgres pg_isready -U lab -d backend_lab
docker compose exec redis redis-cli ping
```

## 停止

```powershell
docker compose down
```

`down` 不删除命名 Volume。只有明确想清空本学习环境数据时才使用 `docker compose down -v`；执行前先确认当前目录和目标 Volume。

## 学习重点

- 宿主机端口与容器端口的区别；
- Service 名为什么能作为 Compose 内 DNS 名；
- 健康检查不等于业务全部正常；
- PostgreSQL 数据为什么在容器重建后仍保留；
- `.env` 为什么不能提交。
