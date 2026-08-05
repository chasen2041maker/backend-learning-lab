# Windows 环境准备

## 第一阶段必须安装

- Git；
- VS Code；
- Python 3.11 或更高版本；
- Go 1.22 或更高版本；
- PowerShell 7（Windows PowerShell 也可完成基础练习和整仓检查）。

检查：

```powershell
git --version
py -0p
python --version
go version
code --version
```

## Python 虚拟环境

虚拟环境让每个项目拥有自己的依赖，不污染其他项目：

```powershell
cd exercises\python-ticket-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
pytest
```

先用 `python --version` 确认版本为 3.11+。如果系统安装了多个 Python，可改用 `py -3.11 -m venv .venv`；如果没有 `py` 命令，直接使用已加入 PATH 的 `python`。

如果 PowerShell 阻止激活，可以不激活，直接执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest
```

整仓检查脚本兼容 Windows PowerShell 5.1 和 PowerShell 7，并会显式检查每个原生命令的退出码：

```powershell
powershell -File scripts/check.ps1
```

## Go 环境

```powershell
cd exercises\go-ticket-api
go env GOPATH
go test ./...
go run ./cmd/server
```

## 第 5 周再安装

- Docker Desktop；
- PostgreSQL 客户端（可选）；
- Redis CLI（可选）。

Docker Desktop 需要启用 WSL2/虚拟化。不要在第一天因为 Docker 问题阻塞 Python 和 Go 基础学习。

## 环境变量

环境变量把配置从代码中分离：

```powershell
$env:APP_ENV = "local"
$env:DATABASE_URL = "postgresql://lab:lab@localhost:5432/backend_lab"
```

不要把密码写进源代码或提交 `.env`。公开仓库只提交 `.env.example`。
