# 第 13 课：Docker、镜像、CI/CD 与 Kubernetes——代码为什么不能“直接扔到服务器上”

初学后端很容易连续听到：

```text
Docker
Image
Container
Registry
CI
CD
Kubernetes
Deployment
Service
Pod
```

然后形成一种模糊印象：

> “代码写完以后，好像要打成 Docker 镜像，再让 K8s 跑。”

方向没错，但如果不知道每一层解决什么问题，就会只会背部署命令。

本课从最原始的问题开始：

> **为什么我电脑上能运行的代码，放到另一台机器上不一定能运行？**

---

# 1. 代码不是完整运行环境

一个 Go 服务可能依赖：

```text
编译后的二进制
环境变量
配置文件
CA 证书
操作系统能力
监听端口
```

Python 服务还可能依赖：

```text
Python 版本
pip packages
系统动态库
```

如果只复制：

```text
main.go
```

到另一台机器，那里甚至未必有 Go 编译器。

如果只复制 Python 源码：

```text
对方可能是不同 Python 版本
依赖没装
系统库不同
```

所以部署问题首先是：

> 如何把应用和它需要的运行环境变成可重复交付的单位？

---

# 2. Docker Image 是什么

可以先把 Image 理解成：

> **一个只读、可版本化的应用运行文件系统模板，加上启动等元数据。**

它通常包含：

```text
基础用户空间
应用文件/二进制
依赖
默认启动命令
```

例如一个 Go 多阶段 Dockerfile：

```dockerfile
FROM golang:1.24 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /out/server ./cmd/server

FROM scratch
COPY --from=build /out/server /server
ENTRYPOINT ["/server"]
```

概念：

```text
build stage
负责把源码编译成产物

runtime stage
只携带运行真正需要的文件
```

不是每个 Go 项目都必须 `scratch`，这里重点是理解 build/runtime 可以分离。

---

# 3. Container 是什么

Container 是：

> **从 Image 启动出来的运行实例。**

关系：

```text
Image
  |
  +-> Container A
  +-> Container B
  +-> Container C
```

类似：

```text
class / instance
```

这个类比只用于区分“模板”和“运行实例”，不要把它理解成编程语言对象完全相同。

---

# 4. Container 不是虚拟机

虚拟机通常包含：

```text
Guest OS Kernel
完整虚拟硬件环境
```

Container 通常：

```text
多个容器共享宿主机 Kernel
通过 namespace/cgroup 等机制隔离进程、网络和资源
```

简化：

```text
Host Kernel
├─ Container A processes/filesystem view
├─ Container B processes/filesystem view
└─ Container C processes/filesystem view
```

所以容器通常比完整 VM 更轻。

但：

```text
Container != 安全沙箱绝对边界
```

仍需要：

- 非 root；
- 最小权限；
- 镜像安全；
- Kernel/Runtime 安全；
- Secret 管理。

---

# 5. Image 为什么是只读模板，但 Container 能写文件

Container 启动时通常会获得可写层：

```text
Image read-only layers
        +
Container writable layer
```

如果容器被删除：

```text
这一层里的临时数据通常也跟着消失
```

因此：

> 不要把必须长期保存的 PostgreSQL 数据只放在容器临时 writable layer。

这就是 Volume 出现的原因之一。

---

# 6. Volume 是什么

Volume 让数据生命周期可以独立于某个 Container：

```text
Container
   |
   v
Volume
```

删除/重新创建 Container：

```text
Volume 仍可存在
```

所以本地 PostgreSQL Compose 常使用 Volume。

但：

```text
有 Volume != 有备份
```

硬盘损坏、误删除、数据损坏仍然需要备份恢复方案。

---

# 7. Port Mapping 是什么

应用在容器内监听：

```text
0.0.0.0:8080
```

Docker 可以映射：

```text
Host 127.0.0.1:8081
        ↓
Container :8080
```

例如：

```powershell
docker run -p 127.0.0.1:8081:8080 my-api
```

这不是“容器自己的 8080 就变成宿主机 8081”。

而是 Docker 建立网络转发规则。

---

# 8. Container Network 解决什么

Compose 中：

```text
api
postgres
redis
```

可以在同一个 Docker network 里通过服务名通信：

```text
api -> postgres:5432
api -> redis:6379
```

注意一个常见坑：

在 `api` 容器里：

```text
localhost
```

指的是：

```text
api 容器自己
```

不是宿主机，也不是 postgres 容器。

所以容器内写：

```text
localhost:5432
```

往往连不到另一个 PostgreSQL container。

---

# 9. Docker Compose 是什么

Compose 用一份配置描述多个本地容器及它们之间的关系：

```yaml
services:
  postgres:
    image: postgres:...
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:...
```

它很适合：

- 本地开发依赖；
- 集成测试环境；
- 小型可重复实验。

Compose 不是 Kubernetes 的“低级版本”。

两者解决场景不同。

---

# 10. 为什么 Image 要放 Registry

你本地 build 出：

```text
my-api:1.0
```

另一台服务器没有这个 Image。

Registry 是存储和分发 Image 的服务：

```text
Developer / CI
    |
    | push
    v
Registry
    |
    | pull
    v
Server / Cluster
```

例如 GitHub Container Registry、ECR、GCR、Docker Hub 等。

---

# 11. Tag 和 Digest 为什么不一样

Tag：

```text
my-api:1.0
my-api:latest
```

是人类友好名称。

Tag 可能被重新指向不同 Image。

Digest：

```text
sha256:...
```

基于内容身份，指向具体不可变镜像内容。

生产部署为了可重复性，常更强调固定 digest：

```text
我部署的是“这一份具体镜像”
```

而不是模糊的：

```text
latest
```

---

# 12. Docker 解决环境一致性，但不自动解决所有问题

Image 可以减少：

```text
依赖版本不同
文件缺失
启动命令不同
```

但不会自动解决：

- 数据库 migration；
- Secret 泄露；
- 应用 bug；
- CPU/内存容量；
- 网络策略；
- 数据备份；
- 下游服务挂掉；
- 日志/指标。

所以：

```text
Dockerized != production-ready
```

---

# 13. 为什么 Container 应尽量非 root

如果容器进程用 root：

```text
一旦应用被攻破
攻击者拿到容器内更高权限
```

最小权限原则：

```text
应用只拥有它真正需要的文件/网络/系统能力
```

因此常见：

- non-root user；
- read-only root filesystem；
- drop capabilities；
- 不把 Docker socket 挂进应用；
- 最小镜像。

这些是降低攻击面，不是绝对安全保证。

---

# 14. CI 到底是什么

CI = Continuous Integration。

核心：

> 代码变化以后，自动在标准环境执行一组集成前验证。

例如 GitHub push：

```text
commit
  ↓
format check
  ↓
lint
  ↓
unit tests
  ↓
contract/integration tests
  ↓
build
```

所以 CI 可以理解为自动验证流水线的一部分。

`pipeline` 是更广泛的“多个自动步骤组成的流程”；CI 是这个流程承担的一种工程目的。

---

# 15. CI 是在本地还是 GitHub 上？

两者都可以有自动化，但 GitHub Actions CI 通常运行在：

```text
GitHub-hosted runner
或
你的 self-hosted runner
```

不是默认在你当前电脑偷偷执行。

所以：

```text
local test
```

和：

```text
CI test
```

是两次不同环境的验证。

---

# 16. 为什么 CI 里要 Build Image

生产发布通常希望部署：

```text
已经被测试过的同一份 artifact
```

而不是：

```text
测试源码 A
部署服务器重新现场 build 源码 B
```

典型：

```text
commit SHA
↓
CI test
↓
build image
↓
scan
↓
push registry
↓
记录 digest
```

后续部署就是选择这个已验证 artifact。

---

# 17. CD 又是什么

CD 可能表示 Continuous Delivery 或 Continuous Deployment，团队用法要看上下文。

简单区分：

```text
Continuous Delivery
产物始终处于可发布状态，发布可能有人确认

Continuous Deployment
通过验证后自动发布到生产
```

不要只记缩写，要看真实 pipeline 是否自动部署。

---

# 18. Deployment 前为什么要 Migration

新代码可能依赖新 schema：

```text
代码开始读取 priority 字段
```

但数据库还没有：

```text
column priority does not exist
```

所以发布必须考虑：

```text
schema change
和
application rollout
```

之间的兼容窗口。

安全演进常倾向：

```text
先 additive schema
→ 新旧代码都能运行
→ rollout 新代码
→ 数据迁移/回填
→ 以后再删除旧字段
```

不是每个 migration 都能简单 `DOWN` 回滚。

---

# 19. Kubernetes 为什么出现

假设现在只有一台机器一个 Container：

```text
手工 docker run
```

还能管理。

但生产可能有：

```text
10 台机器
50 个 API instance
多个 Worker
滚动更新
实例崩溃
节点崩溃
扩缩容
服务发现
Secret/config
```

这时需要一个系统持续管理：

> **我希望系统保持什么状态，以及实际状态偏离时怎么恢复。**

Kubernetes 的核心心智模型就是：

```text
Desired State
      ↓
Controllers continuously reconcile
      ↓
Actual State
```

---

# 20. Kubernetes 不是“管理几个 Docker 容器的 GUI”

更准确：

> Kubernetes 是一个声明式的容器化工作负载编排平台，负责调度、生命周期、服务发现、滚动更新等大量集群级控制。

它不是 Docker 的简单上级命令。

而且现代 Kubernetes 底层不要求 Docker Engine 作为 container runtime。

所以：

```text
Docker 和 K8s 是相关技术层
但不是“Docker 管一个容器，K8s 管很多 Docker”的严格定义
```

---

# 21. Pod 是什么

Kubernetes 最小调度单位是：

```text
Pod
```

一个 Pod 可以包含一个或多个 container，共享部分：

- 网络 namespace；
- localhost；
- volumes。

普通后端 API 常见：

```text
一个 Pod 一个主要应用 container
```

但 Pod 不等于 Container。

---

# 22. Deployment 是什么

Deployment 声明：

```text
我要 3 个 API replicas
使用哪个 image
如何滚动更新
```

例如：

```yaml
spec:
  replicas: 3
```

如果一个 Pod 挂了：

```text
实际 = 2
期望 = 3
```

控制器会尝试创建新的 Pod，让实际回到期望。

这就是 reconcile 思维。

---

# 23. Service 是什么

Pod 会被重建，IP 可能变化。

调用方不应该自己维护：

```text
10.1.2.3
10.1.8.9
...
```

Kubernetes Service 提供稳定的服务访问抽象，并把流量路由到匹配 Pod。

简化：

```text
Caller
  ↓
ticket-service
  ↓
Pod A / Pod B / Pod C
```

注意：

```text
Kubernetes Service
```

和代码里的：

```text
Service layer
```

完全是两个概念。

---

# 24. ConfigMap 和 Secret

ConfigMap：

```text
非敏感配置
```

Secret：

```text
敏感配置的 K8s 对象
```

但：

```text
Secret 名字叫 Secret
!= 数据天然绝对安全
```

仍需：

- RBAC；
- etcd encryption；
- 外部 Secret manager；
- audit；
- 最小权限。

---

# 25. Requests 和 Limits 为什么重要

Pod 可以声明：

```text
CPU request
memory request
CPU limit
memory limit
```

Request 帮 scheduler 判断：

```text
这个节点是否有足够资源放这个 Pod
```

Limit 控制资源上限。

特别注意 memory：

```text
超过 limit
可能被 OOM kill
```

所以资源值不应该抄模板，需要基于监控和压测校准。

---

# 26. Probe 在 Kubernetes 里怎么用

上一课学过：

```text
liveness
readiness
startup
```

K8s 可以根据 probe：

```text
readiness fail
→ 不再把 Service 流量发给它

liveness fail
→ kubelet 可能重启 container
```

错误 probe 会制造事故。

例如数据库暂时挂掉就 liveness fail，可能导致所有 API 反复重启。

---

# 27. Rolling Update 是什么

部署新版本不是：

```text
关掉全部旧服务
再启动全部新服务
```

Deployment 可以逐渐：

```text
旧 Pod ↓
新 Pod ↑
```

让服务继续可用。

但要实现安全滚动：

- readiness 正确；
- graceful shutdown；
- 新旧版本 schema 兼容；
- 下游协议兼容。

K8s 只能执行策略，不能替应用创造兼容性。

---

# 28. Graceful Shutdown 在 K8s 中为什么更重要

Pod 被终止：

```text
SIGTERM
↓
应用停止接新请求
↓
等待正在处理请求
↓
释放资源
↓
退出
```

如果 Go 服务完全不处理 shutdown：

```text
滚动更新时正在处理的请求可能被突然截断
```

所以部署能力会反过来要求应用层正确处理生命周期。

---

# 29. Job 为什么适合 Migration

Migration 是一次性任务：

```text
执行成功后结束
```

和常驻 API Deployment 不同。

Kubernetes Job 可以表达：

```text
运行到成功/失败结束
```

但 migration 仍然要设计：

- 并发只执行一次；
- 超时；
- lock；
- checksum/version；
- 失败停止 rollout。

不是“放进 Job 就安全”。

---

# 30. HPA 是什么

Horizontal Pod Autoscaler 可以根据指标调整副本：

```text
3 replicas
↓ load increases
8 replicas
```

但扩 API Pod 不一定解决瓶颈。

如果真正限制是：

```text
PostgreSQL max connections
第三方 API rate limit
GPU capacity
```

扩更多 Pod 可能让下游更惨。

所以 autoscaling 也必须结合全链容量。

---

# 31. Gateway / Ingress 是什么层

集群里的 Service 提供内部稳定入口。

外部用户还需要进入集群：

```text
Internet
↓
Load Balancer / Gateway / Ingress
↓
Service
↓
Pods
```

现代环境具体使用 Ingress Controller、Gateway API、云 LB 等实现会不同。

本课重点是理解：

```text
外部入口
和
服务内部发现
```

是两个边界。

---

# 32. CI/CD 与 K8s 完整链路

可以画成：

```text
Developer
  ↓ git push
GitHub
  ↓
CI
  ├─ format/lint
  ├─ tests
  ├─ contract
  ├─ secret/vulnerability checks
  └─ build image
       ↓
Registry
       ↓ immutable digest
Deployment process
       ↓
Kubernetes
       ↓
Rolling rollout
       ↓
Readiness / smoke test / metrics
       ↓
continue or rollback
```

这就是“代码怎么变成运行中的服务”的完整工程路径。

---

# 33. Rollback 也不是简单“切回旧镜像”

如果新版本已经：

```text
修改数据库 schema
写入新格式数据
产生新事件
```

旧代码可能已经不能读取。

所以发布需要 backward/forward compatibility。

这也是为什么：

```text
migration 和 deployment 不能分开思考
```

---

# 34. 本仓库怎么练

## 实验 1：Image vs Container

```powershell
docker build ...
docker run ...
docker ps
docker stop ...
docker rm ...
```

解释：

```text
哪一步创建 Image
哪一步创建 Container
删除 Container 后 Image 是否还在
```

## 实验 2：Volume

使用 `exercises/infrastructure`：

```powershell
docker compose up -d
```

写数据库数据，重建 PostgreSQL container，验证 Volume 数据仍在。

然后回答：

```text
这为什么仍不等于完成备份？
```

## 实验 3：Network

从一个容器内解释：

```text
localhost
postgres
host.docker.internal
```

分别指向什么。

## 实验 4：CI

打开 `.github/workflows/ci.yml`，逐个说明：

```text
trigger
runner
steps
失败会阻止什么
```

## 实验 5：K8s dry-run

```powershell
kubectl apply --dry-run=client -f exercises/reliability-labs/k8s/deployment.yaml
```

读懂：

- image；
- replicas；
- resources；
- securityContext；
- probes。

不要求先维护真实 K8s 集群。

---

# 35. 常见误区

## Docker = 虚拟机

错误。容器通常共享宿主 Kernel。

## Docker 把“代码和操作系统全部打包”

过度简化。Image 包含用户空间文件/运行内容，不包含一个独立 Guest Kernel。

## 删除 Container 数据一定没了

不一定。Volume 可以独立存在。

## Volume = Backup

错误。

## CI = 测试

不完整。CI 是自动集成验证流程，测试只是其中一步。

## Pipeline = CI

不完全等同。Pipeline 是一般的自动化步骤链，CI/CD 可以由 pipeline 实现。

## K8s = 更高级 Docker

错误。K8s 是集群级声明式编排和 reconciliation 系统。

## 上 K8s 才算生产后端

错误。很多系统完全可以不需要 K8s。

## HPA 能解决所有高流量

错误。真正瓶颈可能在数据库或外部供应商。

---

# 36. 关闭文档复述

1. 为什么源码本身不是完整部署产物？
2. Image 和 Container 什么关系？
3. Container 和 VM 的核心区别是什么？
4. 为什么 Container 删除后业务数据库不应该跟着丢？
5. Volume 为什么不是 Backup？
6. 容器内 `localhost` 指谁？
7. Registry 解决什么？
8. Tag 和 Digest 为什么不一样？
9. CI 和 Pipeline 的关系是什么？
10. 为什么常见流程是“测试后 build artifact”，而不是每台生产机自己现场 build？
11. Kubernetes 的 desired state / reconciliation 是什么？
12. Pod 和 Container 什么关系？
13. Deployment 和 Service 分别解决什么？
14. Readiness 和 Liveness 如何影响 K8s 行为？
15. 为什么 Rolling Update 仍要求应用自己兼容新旧 schema？
16. 为什么扩更多 Pod 可能反而压垮数据库？
17. 为什么 Rollback 不能只考虑镜像版本？

能把 `git push -> CI -> image -> registry -> deploy -> running instance` 这一条链画清楚，比会背几十条 Docker/K8s 命令重要得多。
