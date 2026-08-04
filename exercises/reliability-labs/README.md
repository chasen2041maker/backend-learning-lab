# 后端可靠性微实验

这些文件把课程中容易“只看懂、没跑过”的知识拆成可执行微实验，只使用 Python 标准库。先运行测试，再故意改坏一个不变量观察失败。

```powershell
python -m unittest discover -s exercises/reliability-labs/tests -v
python exercises/reliability-labs/metrics_demo.py
curl http://127.0.0.1:8081/metrics
```

| 文件 | 要证明的事情 |
| --- | --- |
| `concurrency_timeout.py` | 并发必须有上限，每个下游必须有超时，单点失败不无限拖住整体 |
| `authorization.py` | Authentication 产生可信身份；Authorization 每次检查租户、权限和资源；有副作用的 Agent Tool 还需确认与幂等键 |
| `webhook_security.py` | 对原始字节验 HMAC、限制时间窗、按事件 ID 去重 |
| `outbox_worker.py` | claim/lease/fencing、有限重试、DLQ 和旧 Worker 拒绝 |
| `fake_rag.py` | 检索先按租户过滤，再受结果预算限制，并返回来源 |
| `metrics_demo.py` | liveness、readiness 和 Prometheus 文本指标是不同信号 |

## Docker 与 K8s 阅读实验

```powershell
docker build -t backend-learning-metrics:0.1.0 exercises/reliability-labs
docker run --rm -p 127.0.0.1:8081:8081 backend-learning-metrics:0.1.0
kubectl apply --dry-run=client -f exercises/reliability-labs/k8s/deployment.yaml
```

K8s 文件用于学习资源预算、非 root、只读根文件系统和 Probe，不要求你维护真实集群。生产部署应把版本 Tag 换成构建生成的镜像 digest。
