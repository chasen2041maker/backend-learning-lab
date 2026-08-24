# Windows 环境准备：按当前任务安装，不一次装全家桶

目标不是把电脑配置成“看起来像后端工程师”，而是让当前正在学的代码能稳定运行，并且你知道每个工具是谁在调用。

## 1. 基础工具

建议先有：

- Git；
- VS Code；
- Go 1.22+；
- Python 3.11+；
- PowerShell 7（Windows PowerShell 5.1 也能完成基础检查）。

检查：

```powershell
git --version
go version
python --version
python -c "import sys; print(sys.executable)"
code --version
```

如果某条命令提示“无法识别”，先解决 PATH/安装问题，不要马上继续装框架。

## 2. Go：当前学 Go 时最少需要什么

进入 Go 练习：

```powershell
cd exercises\go-ticket-api
go env GOMOD
go env GOPATH
go test ./...
go run ./cmd/server
```

### `go.mod` 是什么

`go.mod` 描述一个 Go Module：

```text
这个模块叫什么
使用哪个 Go 版本
依赖哪些外部模块
```

它不是“为了 VS Code 才创建的文件”，也不是 Docker/虚拟环境。

Go 工具链根据它判断当前代码属于哪个 module，并解析 import/依赖。

基础阶段优先标准库，不要因为一个 HTTP Handler 就先安装 Gin、GORM 等框架。

## 3. Python：确认 pip 属于同一个解释器

本仓库可以直接使用当前 PATH 中的 Python，不强制虚拟环境；但必须先确认 `python` 和 pip 是同一套解释器：

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
```

安装仓库依赖：

```powershell
cd exercises\python-ticket-api
python -m pip install -r ..\..\requirements-repo.lock
python -m pip install --no-deps -e .
python -m pytest
```

优先使用：

```powershell
python -m pip ...
```

而不是不确定归属的裸 `pip`。

典型错误：

```text
我明明 pip install 了
但运行还是 ModuleNotFoundError
```

常见原因是：安装包的 Python 和运行程序的 Python 不是同一个解释器。

先比较：

```powershell
where.exe python
python -c "import sys; print(sys.executable)"
python -m pip --version
```

## 4. Docker：什么时候再装/再管

只有当当前练习真的需要 PostgreSQL、Redis 或容器实验时，再处理 Docker Desktop。

Docker 不是运行普通 Go/Python 代码的前置条件。

Windows 上 Docker Desktop 通常依赖 WSL2/虚拟化。如果 Docker 安装卡住，不应该阻塞：

- Go 语法；
- `net/http`；
- Handler 测试；
- 内存 Repository；
- HTTP/JSON 基础。

需要基础设施时，再进入：

```powershell
cd exercises\infrastructure
docker compose up -d
docker compose ps
```

## 5. PostgreSQL / Redis CLI 不是必须同时安装

本仓库的 PostgreSQL/Redis 可以通过 Docker Compose 提供。

CLI 只有在你需要手工观察时才安装，例如：

```text
psql
redis-cli
```

不要因为“后端以后会用”就在第一天把所有工具都装一遍。

## 6. 进程、端口和监听地址

启动一个服务后，要能回答：

```text
哪个进程在运行？
监听哪个 IP？
监听哪个 Port？
本机还是局域网可访问？
```

Windows 可查看端口：

```powershell
Get-NetTCPConnection -State Listen |
  Select-Object LocalAddress,LocalPort,OwningProcess
```

根据 PID 查进程：

```powershell
Get-Process -Id <PID>
```

例如：

```text
127.0.0.1:8081
```

表示只监听本机 loopback；不是“服务器已经发布到互联网”。

## 7. 环境变量

环境变量把运行配置从代码中分离，例如 PowerShell：

```powershell
$env:APP_ENV = "local"
$env:JWT_SECRET = "local-development-only-value"
```

代码读取配置，不把 Secret 写死进 Git：

```text
source code
    ↓
read environment
    ↓
runtime config
```

数据库连接也可以这样提供：

```powershell
$env:DATABASE_URL = "postgresql://lab:lab@localhost:5432/backend_lab"
```

公开仓库只提交 `.env.example`，不要提交真实 `.env`、API Key、Token 或密码。

## 8. 代理和网络问题要和代码问题分开

如果工具连接外网失败，先区分：

```text
代码错误？
DNS？
代理端口？
代理进程？
TLS？
远端服务？
```

例如本地代理通常表现为某个 `127.0.0.1:<port>` 进程正在监听。代理掉线和 Go 编译失败是两个完全不同层面的故障。

## 9. VS Code 的职责

VS Code + Go 扩展 / gopls 可以提供：

- 语法诊断；
- 自动补全；
- 跳转定义；
- `gofmt`；
- 测试入口。

但 IDE 绿色不等于程序行为正确。最终仍以：

```powershell
go test ./...
```

和真实请求/测试结果为准。

## 10. 整仓检查

根目录可以运行：

```powershell
powershell -File scripts/check.ps1
```

它用于发现格式、测试、契约、链接等问题。

如果某项依赖尚未安装，应该把它当作“当前环境没有这项验证能力”，而不是假装检查通过。

## 复述检查

关闭文档后回答：

1. `go.mod` 解决什么问题？
2. 为什么 `python -m pip` 比裸 `pip` 更容易避免解释器错位？
3. 为什么 Docker 不是写 Go HTTP Server 的前置条件？
4. `127.0.0.1:8081` 分别代表什么？
5. 环境变量和代码常量有什么边界区别？
6. 为什么代理故障不能直接归类为“代码坏了”？
