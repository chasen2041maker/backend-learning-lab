# Scripts：仓库自动验证入口

`scripts/` 保存的是这个学习仓库自己的质量检查工具。

它们的目标不是把仓库变成复杂平台，而是防止几类非常常见的学习仓库退化：

```text
文档链接失效
Python / Go 示例悄悄坏掉
两个实现和契约漂移
真实 Secret 被误提交
本地说“通过”但某个命令其实失败
```

---

## 一键本地检查：`check.ps1`

Windows PowerShell：

```powershell
powershell -File scripts/check.ps1
```

如果希望本地没有 Docker 也必须失败：

```powershell
powershell -File scripts/check.ps1 -RequireDocker
```

脚本当前检查：

- Python 3.11+；
- Go / gofmt / Git；
- Python 开发依赖；
- `git diff --check`；
- contract validation；
- Markdown link check；
- Secret/private-data scan；
- Ruff format/lint；
- Python tests；
- reliability/Redis unittest；
- Go formatting / vet / test；
- 可用时 `go test -race`；
- 可用时 Docker Compose rendering。

脚本遇到 native command 非 0 exit code 会失败，不会在中途失败后仍打印“全部通过”。

---

## `validate_contracts.py`

检查 HTTP / Event 机器契约本身是否满足仓库约定的结构和关键不变量。

它防的是：

```text
文档写一个规则
机器 case/schema 已经变成另一套
```

但它不会替你判断业务契约是否设计合理。

---

## `check_markdown_links.py`

检查仓库内部 Markdown 相对链接。

重构目录、改文件名、新增索引页以后都应该跑。

它证明的是：

```text
目标文件存在
```

不证明链接目标内容一定正确。

---

## `scan_secrets.py`

对公开仓库做最低限度的敏感信息扫描。

它是防漏网，不是完整 DLP/Secret 管理系统。

即使扫描通过，提交前仍然必须人工确认没有：

- 公司代码；
- 内部 URL；
- 客户/用户数据；
- 真实日志；
- API Key / Token / Password；
- 私有 Prompt / 配置。

安全规则见 [`../SECURITY.md`](../SECURITY.md)。

---

## CI 和本地脚本是什么关系

GitHub Actions：[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml)

CI 会在标准环境重新运行核心检查，并额外运行 Docker/PostgreSQL/Redis 集成验证和 smoke test。

所以：

```text
本地检查通过
≠ CI 必然通过

CI 通过
≠ 生产 ready

测试全部绿
≠ 学习者已经理解
```

CI 只能证明**已经编码进检查系统的行为**当前没有被破坏。

---

## 什么时候应该新增脚本

只有当一个仓库级错误：

```text
容易重复出现
可以稳定自动判断
人工检查成本明显更高
```

才值得新增自动检查。

不要为了“工程化”把几十个一次性命令包装成复杂脚本框架。

优先保持：

```text
小
明确
失败可读
本地和 CI 语义一致
```
