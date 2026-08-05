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

## 使用当前 Python 环境

本仓库直接使用 PATH 中的 `python`，不要求创建虚拟环境。先确认版本和解释器位置：

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

版本必须是 Python 3.11 或更高。随后安装整仓固定依赖和本地包：

```powershell
cd exercises\python-ticket-api
python -m pip install -r ..\..\requirements-repo.lock
python -m pip install --no-deps -e .
python -m pytest
```

如果系统安装了多个 Python，确认 `python` 和 pip 属于同一个解释器：

```powershell
python -c "import sys; print(sys.executable)"
python -m pip --version
```

不要混用裸 `pip`、`py -3.x` 和另一个路径下的 `python`。典型症状是包明明安装过，
运行时却出现 `ModuleNotFoundError`，或二进制扩展文件名中的 Python 版本与
`python --version` 不一致。此时用当前解释器重新安装：

```powershell
python -m pip install --force-reinstall -r ..\..\requirements-repo.lock
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
