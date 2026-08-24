# 后端可靠性微实验：专门制造“Happy Path 看不出来”的失败

这个目录不是一个业务服务，而是一组**最小故障实验**。它们用于验证那些看文档很容易点头、真正出故障时却最容易混乱的概念：timeout、权限、Webhook 重放、Outbox、stale worker、RAG tenant filter、Probe 与 metrics。

先运行完整基线：

```powershell
python -m unittest discover -s exercises/reliability-labs/tests -v
```

不要只记住 green。每个文件至少要亲手改坏一次，再看测试如何抓住不变量。

## 实验地图

| 文件 | 关键不变量 | 故意改坏什么 |
| --- | --- | --- |
| `concurrency_timeout.py` | 并发有上限；慢依赖不能无限拖住整体 | 去掉 semaphore/timeout |
| `authorization.py` | Authentication 只产生身份；每个资源/Tool 仍要 Authorization | 相信客户端 tenant 或跳过 permission |
| `webhook_security.py` | 对原始字节验 HMAC；成功后去重；失败可重试 | 先 parse 再重新序列化签名，或失败也标 processed |
| `outbox_worker.py` | lease/fencing 阻止旧 Worker 写回；retry 有上限 | 只检查 worker_id，不检查 lease token |
| `fake_rag.py` | tenant/ACL filter 在模型看到资料之前完成 | 先全库检索再让模型“不要泄露” |
| `metrics_demo.py` | liveness/readiness/metric 是三类不同信号 | DB 不可用时让 liveness 也直接失败 |

## 1. Concurrency / Timeout

你要能解释：

```text
为什么 goroutine/task 很轻
≠
可以无限创建并发下游请求
```

观察最大并发、单个 timeout、整体 wall-clock budget。修改时特别注意 retry 会不会把流量再放大。

## 2. Authorization

这个实验延续认证课程的总原则：

```text
client/model output
= 不可信输入

server-validated Principal
= 身份依据
```

即使 Agent 已经选择了某个 Tool，也仍然要检查 permission、tenant/owner、必要 confirmation 与 idempotency。

## 3. Webhook Security

重点不是 HMAC 函数怎么调用，而是顺序：

```text
raw request bytes
→ timestamp/replay window
→ signature verification
→ parse/validate
→ dedupe/business transaction
→ success
```

如果业务处理失败，不能提前永久标记 processed，否则 Provider retry 会被错误吞掉。

## 4. Outbox Worker

关注 stale worker：

```text
Worker A claim
→ 卡住
→ lease 过期
→ Worker B reclaim
→ A 又恢复
```

如果没有 fencing，A 可能覆盖 B 的新结果。lease 只说明“暂时拥有”，fencing 才用于拒绝过期持有者的写回。

## 5. Fake RAG

这里只使用 deterministic fake，故意不讨论模型质量。要证明：

```text
Principal
→ tenant filter
→ relevant sources
→ answer
```

没有相关来源时抛出 `NoRelevantSources`，而不是编造一个看起来合理的内部答案。

## 6. Metrics / Probe

运行：

```powershell
python exercises/reliability-labs/metrics_demo.py
curl http://127.0.0.1:8081/metrics
```

理解：

```text
liveness  = 进程要不要重启
readiness = 现在要不要接新流量
metrics   = 给人/系统观察趋势和原因
```

不要把“数据库挂了”机械等同于“进程必须被 Kubernetes 重启”。

## Docker / K8s 阅读实验

```powershell
docker build -t backend-learning-metrics:0.1.0 exercises/reliability-labs
docker run --rm -p 127.0.0.1:8081:8081 backend-learning-metrics:0.1.0
kubectl apply --dry-run=client -f exercises/reliability-labs/k8s/deployment.yaml
```

这里验证的是 non-root、只读根文件系统、resources、Probe 等配置能被读懂/校验，不代表已经完成生产部署。

## 每个微实验的验收

完成一个文件后记录：

```text
正常不变量：
我故意破坏：
测试/现象：
失败为什么危险：
最小修复：
生产还需要补什么：
```

如果你只能描述代码，却说不清“它在防哪个失败窗口”，这个实验还没有真正完成。
