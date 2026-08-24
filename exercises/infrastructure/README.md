# 本地 PostgreSQL 与 Redis：先理解“依赖为什么存在”，再运行 Compose

这个目录只提供**本机学习依赖**。它不是生产基础设施模板，也不代表后端项目一开始就应该同时启动 PostgreSQL 和 Redis。

只有当当前实验明确需要外部依赖时再启动。

## 启动

```powershell
Copy-Item .env.example .env
docker compose up -d
docker compose ps
```

验证：

```powershell
docker compose exec postgres pg_isready -U lab -d backend_lab
docker compose exec redis redis-cli ping
```

停止：

```powershell
docker compose down
```

`down` 不删除命名 Volume。只有你明确要清空学习数据时才使用：

```powershell
docker compose down -v
```

执行前确认当前目录和 Volume，不要把“重装环境”当成默认排障方式。

## 这个实验真正要理解的 5 个对象

```text
Image      -> 可版本化的运行模板
Container  -> Image 启动后的进程/隔离实例
Network    -> 容器之间如何发现和通信
Port       -> 宿主机入口如何转发到容器
Volume     -> 数据生命周期如何独立于容器
```

### 容器里的 `localhost`

如果 API、PostgreSQL、Redis 分别是不同 Container：

```text
API container 中 localhost
= API 自己
```

不是 PostgreSQL，也不是宿主机。

Compose 内部通常通过 service name：

```text
postgres:5432
redis:6379
```

通信。

## PostgreSQL 和 Redis 的角色不同

这个仓库默认心智模型：

```text
PostgreSQL
= 业务事实源

Redis
= cache / session / rate limit / coordination / stream 等运行时角色
```

每次使用 Redis 前必须先回答：

```text
这个 Key 丢了会怎样？
能否从 PostgreSQL/其他事实源重建？
Redis 挂了应该 fail-open、fail-closed 还是降级？
```

不要因为 Compose 已经有 Redis，就在每个功能里强行使用。

## 健康检查不等于业务正确

`pg_isready` / `PING` 只说明服务在某个层面可响应，不证明：

- schema 已正确 migration；
- 当前账号有正确权限；
- 查询不会 timeout；
- Redis 数据语义正确；
- API 依赖链整体可用。

所以：

```text
container healthy
≠
application ready
```

## Volume 不等于 Backup

命名 Volume 能让容器删除后数据仍存在，但不能解决：

- 宿主磁盘损坏；
- 人为 `down -v`；
- 逻辑误删除；
- 数据文件损坏；
- 灾难恢复。

生产环境需要独立 backup/restore 策略。

## 安全边界

- `lab/lab` 只用于本机学习；
- Redis 实验未配置生产级认证；
- 宿主端口显式绑定 `127.0.0.1`；
- 不要为了“手机也能访问”随手改成 `0.0.0.0`；
- `.env` 不提交；
- 不把真实公司数据库/Redis 地址填进这个公开仓库。

检查监听：

```powershell
docker compose ps
docker port <container>
```

确认宿主机入口符合预期。

## Tag 与 Digest

Compose 同时使用可读 Tag 和 digest，是为了：

```text
人知道大版本
+
机器拿到确定内容
```

升级时不要只删 digest 追求“自动最新”。更好的流程：

```text
读 release/security notes
→ 修改版本
→ 拉取并记录新 digest
→ 启动
→ 运行 schema/cache/recovery 实验
→ 再提交
```

## 关闭文档后应该能回答

1. 删除 Container 和删除 Volume 分别会怎样？
2. 为什么 API Container 里不能用 `localhost:5432` 找另一个 Container？
3. Redis flush 后哪些数据应该还能恢复？
4. `pg_isready` 成功为什么不代表业务 API ready？
5. 为什么本地弱口令必须配合 loopback 限制？
