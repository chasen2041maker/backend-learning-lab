# 第 1 课实验：把“请求失败”拆成网络层和 HTTP 层

先阅读 [`lessons/01-request-lifecycle.md`](../../lessons/01-request-lifecycle.md)。本目录不启动第二套服务，而是让你把已经观察到的请求结果整理成**可测试的判断逻辑**。

## 这个实验要证明什么

很多初学者看到请求失败，只会说：

```text
接口报错了
```

但后端排障首先要分层：

```text
有没有建立连接？
    ↓
有没有收到 HTTP Response？
    ↓
HTTP status 是什么？
    ↓
Body 里有没有稳定 machine code？
    ↓
request ID 能不能把日志串起来？
```

本实验最终要让你能区分：

- `connection refused`：没有 HTTP Response；
- `404/422/500`：已经进入 HTTP 世界；
- `X-Request-ID` 和 JSON `request_id`：用于关联同一次请求，不是业务 ID。

## 允许修改的范围

只修改：

```text
starter/observations.py
```

不要修改测试来迎合实现。

## 第一步：先保留失败

```powershell
python -m pytest exercises/01-request-lifecycle/tests -v -p no:cacheprovider
```

第一次应看到 TODO/`NotImplementedError` 导致失败。先读失败信息，再打开实现。

## 两个函数分别在表达什么

### 网络错误

输入里没有有效 HTTP response 时，你不能编造：

```text
status=500
```

因为 500 是服务器已经返回的 HTTP 状态。连接都没建立时，应该保持“网络层失败”的语义。

### HTTP 错误

如果已经收到 Response，优先使用稳定字段：

```text
status code
machine-readable code
request_id
```

不要让程序通过解析英文 `message` 决定下一步。

## 完成后的证据

再次运行：

```powershell
python -m pytest exercises/01-request-lifecycle/tests -v -p no:cacheprovider
```

预计：

```text
3 passed
```

但 `3 passed` 只证明这两个小函数满足当前测试，不代表你已经会网络排障。

再口头回答：

1. 为什么 `connection refused` 不能写成 HTTP 500？
2. 401 和 403 为什么都说明已经收到了 HTTP Response？
3. request ID 和 ticket ID 的生命周期有什么区别？
4. 如果 Header 的 request ID 和 Body 不一致，你排障时会出现什么问题？

## 故意改坏一次

把实现临时改成“所有错误都返回 500”，重新跑测试，观察哪条断言失败。然后恢复正确实现。

这个故障实验比只看最终 green 更重要：它证明**错误分类本身就是外部契约的一部分**。

卡住时按顺序查看 [`hints.md`](hints.md)，一次只看一级。
