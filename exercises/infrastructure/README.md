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

## 安全边界

- `lab/lab` 仅用于本机学习，绝不能用于共享服务器或生产环境；
- Redis 实验没有配置认证，因此端口显式绑定到 `127.0.0.1`；
- 不要把端口改成 `0.0.0.0`，也不要删除 Compose 中的 loopback 地址；
- `docker compose ps` 和 `docker port` 应显示宿主机监听地址为 `127.0.0.1`。

## 版本更新

Compose 同时固定可读版本 Tag 和镜像 digest，避免同一个 Tag 日后指向不同内容。升级时先阅读 PostgreSQL/Redis release notes，在分支中修改 Tag，拉取并记录新的 digest，执行 schema、缓存和恢复实验后再提交；不要只删掉 digest 追求“自动最新”。
