# 公开学习仓库安全规则：先判断“能不能公开”，再判断“技术上有没有用”

这个仓库是公开的。它可以保存后端工程原理、原创实验和虚构业务，但**不能因为内容有学习价值，就把真实工作环境的信息搬进来**。

## 提交前必须检查

禁止提交：

- 公司/雇主源代码、内部 SDK、私有 Prompt、内部架构文档；
- 内部域名、IP、VPN、数据库地址、服务发现地址；
- API Key、Access Token、Refresh Token、Cookie、JWT、私钥、密码；
- `.env`、云凭证、kubeconfig、真实 Secret manifest；
- 客户/用户/同事身份信息、真实业务数据和原始日志；
- 带真实账号、邮箱、浏览器登录态、终端 Secret 的截图；
- 从公司仓库“改几个名字”后直接复制出来的实现。

可以提交：

- 自己从零写的最小示例；
- `tenant_a`、`tenant_b`、`req_demo_001` 等虚构数据；
- `.env.example` 中明确的本地假值；
- 脱离真实公司业务后仍能独立表达工程原理的原创实验。

## Secret 的原则

```text
Secret value
→ 不进 Git
→ 不进文档
→ 不进测试快照
→ 不进日志
→ 不进聊天后再复制回公开仓库
```

`JWT_SECRET`、数据库密码等示例应使用占位符：

```text
JWT_SECRET=<set-a-high-entropy-secret>
```

不要为了“示例能直接运行”而提交真实凭证。

## `.env.example` 和 `.env` 的区别

`.env.example` 描述**需要哪些变量和安全的本地示例格式**；`.env` 保存当前环境真实值，因此必须被 `.gitignore` 排除。

如果某个本地实验使用 `lab/lab` 这种弱口令，文档必须明确：

```text
仅绑定 127.0.0.1
仅用于本机学习
不能复制到共享服务器/生产
```

## 日志与截图最容易漏什么

提交日志前检查：

```text
Authorization header
Cookie
query string token
数据库 DSN
Prompt 中的业务秘密
用户 email/phone/id
内部 hostname/path
```

截图比纯文本更危险，因为浏览器头像、书签、终端上一条命令、侧边栏项目名都可能暴露信息。

## 依赖与镜像

公开学习仓库也应避免：

- 镜像里 COPY `.env`；
- Docker build context 带不必要 Secret；
- `latest` 造成无法复现的教学环境；
- 已知高风险依赖长期不处理。

固定 digest 是为了复现，不代表镜像天然安全；升级仍要看 release/security notes 并重新验证。

## 如果已经误提交 Secret

只从最新文件删除**不够**，因为 Git 历史可能仍保存它。

立即：

1. 撤销/轮换泄露凭证；
2. 判断是否需要清理 Git 历史；
3. 检查 forks/cache/CI logs/artifacts；
4. 记录根因，补 `.gitignore` / secret scan / 流程防线；
5. 不要继续使用“反正仓库删掉了”的旧 Secret。

## 不确定能不能公开时

默认不提交。重新构造一个虚构最小场景：

```text
真实内部工单系统事故
        ↓ 抽象问题
COMMIT 后响应丢失导致客户端重试
        ↓ 原创实验
Ticket + Idempotency Key + fake data
```

我们要保留的是工程原理，不是原始业务材料。
