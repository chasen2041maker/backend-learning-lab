# 第 11 课：测试、调试与代码审查——不是“有没有报错”，而是你证明了什么

后端代码能启动，只能证明：

```text
程序至少启动了
```

一个接口手工请求成功，也只能证明：

```text
这一个输入在这一次运行里成功了
```

真正的工程问题是：

> **边界条件、数据库、并发、失败恢复、兼容性以后还会不会正确？出了问题以后，你能不能靠证据定位，而不是靠猜？**

所以测试和 Debug 不是“写完功能以后的附加步骤”，而是后端设计的一部分。

---

# 1. 测试到底在干什么

测试不是为了得到：

```text
100% coverage
```

而是为了留下一个可重复的证明：

```text
给定这个前置状态
当发生这个行为
外部可观察结果必须满足这些条件
```

经典结构：

```text
Arrange
准备状态和依赖

Act
执行行为

Assert
验证结果
```

例如：

```text
Arrange: ticket version=3
Act: 用 expected_version=2 请求关闭
Assert: 返回冲突，而且 ticket 仍是 open/version=3
```

这个测试证明的是一个并发业务边界，而不是某个内部函数被调用了几次。

---

# 2. 不同测试层证明不同东西

| 类型 | 主要证明 | 它不能单独证明 |
| --- | --- | --- |
| Unit | 业务规则、纯函数、状态机、错误分支 | SQL 真能跑、网络协议正确 |
| Handler/API test | HTTP 输入输出、状态码、Header、JSON | 真实 PostgreSQL 行为 |
| Repository integration | SQL、constraint、transaction、driver | 完整用户链路 |
| Contract | 多实现/多服务是否遵守同一外部行为 | 内部业务逻辑完全正确 |
| E2E | 多组件关键路径能串起来 | 所有边界情况都覆盖 |
| Fault test | timeout、重复、宕机窗口、恢复 | 正常业务所有规则 |
| Load test | 容量、延迟、资源拐点 | 功能逻辑完全正确 |

所以：

```text
unit tests passed
```

不能推导：

```text
生产数据库一定没问题
```

同理：

```text
E2E 通过
```

也不能推导：

```text
所有异常路径都验证了
```

---

# 3. Unit Test 什么时候最有价值

适合不需要真实外部系统就能判断的规则：

```text
状态能不能转换
输入归一化
错误映射
权限规则
重试分类
预算计算
```

例如：

```text
open -> closed     allowed
closed -> open     forbidden
```

这种规则如果必须启动 PostgreSQL 才能测试，会让反馈变慢，而且把本来简单的业务规则和基础设施绑在一起。

---

# 4. Integration Test 为什么不可替代

Repository 代码：

```text
看起来 SQL 正确
```

和：

```text
真实 PostgreSQL 下真的正确
```

不是同一件事。

真实集成测试可以证明：

- schema 能创建；
- constraint 真生效；
- SQL 方言正确；
- transaction rollback 行为符合预期；
- driver 类型转换正确；
- lock / timeout 行为真实存在。

例如 SQLite fake 通过，并不能自动证明 PostgreSQL 的：

```text
UUID
timestamptz
FOR UPDATE
SKIP LOCKED
isolation semantics
```

都一样。

---

# 5. Fake / Mock / Stub 不要混成“假东西”

术语在不同团队用法会有差异，但可以先抓语义。

## Stub

提供预设返回：

```text
调用 fakeWeather()
→ 永远返回 25°C
```

主要让测试有可控输入。

## Fake

有一个简化但真的可运行实现：

```text
InMemoryRepository
```

它可能保存数据，但不具备真实 PostgreSQL 的所有语义。

## Mock

常用于验证交互：

```text
SendEmail 必须调用一次
```

问题是：过度 mock 会把测试绑死内部实现。

更值得优先验证：

```text
最终可观察行为
```

而不是：

```text
内部函数调用顺序刚好跟今天一样
```

---

# 6. 测试最怕什么：测试实现，不测试行为

脆弱测试：

```text
assert repository.Save called once
assert helperA called before helperB
```

如果重构内部结构但行为完全没变，测试全坏。

更稳定：

```text
创建成功后返回 201
数据库只存在一条 ticket
tenant B 无法读取
重复 idempotency key 返回同一 resource
```

这就是 behavior-oriented testing。

---

# 7. Table-driven Test 为什么在 Go 中很常见

多个输入共享同一行为结构：

```go
tests := []struct {
    name       string
    method     string
    wantStatus int
}{
    {"get", http.MethodGet, 200},
    {"post rejected", http.MethodPost, 405},
}
```

优点：

- 边界输入一眼可见；
- 新增 case 成本低；
- 减少重复测试代码。

但如果每个 case 有完全不同的 setup/assert，硬塞进一张巨大表反而更难读。

---

# 8. Regression Test 是怎么来的

真实 bug：

```text
跨租户通过 compact UUID 绕过校验
```

正确修复流程：

```text
先写一个能稳定复现 bug 的失败测试
↓
确认它真的失败
↓
修代码
↓
测试通过
↓
保留这个测试
```

这个测试以后就变成 regression test：

```text
防止同一个 bug 回来
```

如果修 bug 前测试就是绿的，要怀疑：

> 这个测试到底有没有复现真正问题？

---

# 9. Test Coverage 能告诉你什么

Coverage 可以告诉：

```text
哪些代码行/分支在测试中执行过
```

但不能告诉：

```text
断言是否正确
边界是否选对
业务不变量是否完整
测试是不是只执行但没检查
```

所以：

```text
95% coverage
```

可能仍然有严重 bug。

Coverage 是找盲区的工具，不是质量分数。

---

# 10. Contract Test 为什么特别适合这个仓库

这个仓库有 Python/Go 两套 API 实现。

如果每套测试自己写预期：

```text
Python 认为 unknown field -> 422
Go 认为 unknown field -> 201
```

两边测试都可能各自绿。

共享契约：

```text
contracts/http-cases.json
```

让两个实现读取同一组行为期望。

它证明：

> 不同实现没有悄悄把外部 API 语义改成两套。

这就是 contract test 的价值。

---

# 11. E2E 为什么应该少而关键

E2E 可能：

```text
启动 API
启动 DB
启动 Redis
真正发请求
验证最终结果
```

好处：

```text
证明真实组件能连起来
```

代价：

- 慢；
- 环境复杂；
- 失败定位困难；
- 更容易 flaky。

所以不要把所有边界都塞进 E2E。

通常：

```text
少量关键路径 E2E
+
大量更小、更快的 unit/integration/contract tests
```

更稳定。

---

# 12. Flaky Test 是什么

同一代码：

```text
有时 pass
有时 fail
```

而输入没有刻意变化。

常见原因：

- 真实时间；
- sleep 猜时序；
- 并发 race；
- 网络依赖；
- 共享测试数据；
- 顺序依赖；
- 随机数没有固定 seed。

不要解决成：

```text
CI 再跑一次，绿了就算
```

偶发失败本身就是系统边界不清的信号。

---

# 13. 为什么 `time.Sleep` 很容易写出脆弱并发测试

测试：

```text
启动 goroutine
sleep 100ms
假设它已经完成
```

机器慢一点：

```text
100ms 不够
```

机器快一点：

```text
浪费时间
```

更好是等待真实同步条件：

- channel；
- WaitGroup；
- context；
- polling with bounded deadline；
- fake clock。

测试应该等事件，而不是猜时间。

---

# 14. Debug 的第一步不是“改代码”

推荐顺序：

```text
1. 明确预期
2. 稳定复现
3. 保存实际结果
4. 找第一个错误状态
5. 提一个可证伪假设
6. 做最小实验
7. 修根因
8. 回归验证
```

如果一上来就改三处代码：

```text
最后好了
```

你仍然不知道真正原因是什么。

---

# 15. “第一个错误状态”非常重要

调用链：

```text
Browser
→ Gateway
→ Service
→ Redis
→ Database
```

最后用户看到：

```text
500 Internal Server Error
```

500 只是最后表现。

真正第一个错误可能是：

```text
DB unique violation
```

然后 Service 错误映射错了，Gateway 又包成 500。

调试要找：

> 数据/控制流第一次偏离预期的位置。

---

# 16. Request ID / Trace ID 如何帮助 Debug

如果并发有 1000 个请求，日志：

```text
error calling database
request succeeded
retrying
```

根本不知道哪些属于同一次请求。

使用：

```text
request_id=req_123
```

让一次入口请求的日志可以串起来。

跨服务再使用：

```text
trace_id
```

但是：

```text
ID 本身不会自动解决问题
```

只有每层正确传播并写入结构化日志，它才有价值。

---

# 17. 一个好 Bug Report 至少有什么

不要只发：

```text
为什么报错？
```

至少：

```text
目标：我要完成什么
预期：应该怎样
实际：发生什么
复现：具体步骤
完整错误：不是最后一行
环境：必要版本
已验证事实：哪些不是猜测
当前假设：我认为可能是什么
```

这会大幅提高 AI、同事和未来自己的调试质量。

---

# 18. 日志不能替代测试

日志是：

```text
运行以后留下证据
```

测试是：

```text
主动执行一个条件并判断结果
```

你不能因为日志里“看起来没问题”，就认为边界已验证。

同样，也不能只靠测试完全替代生产观测。

两者职责不同。

---

# 19. 故障注入为什么有价值

某些可靠性结论正常路径永远证明不了。

例如要证明：

```text
数据库提交后响应丢失不会重复创建
```

就必须故意制造：

```text
commit 后
return 前
失败
```

要证明：

```text
consumer ACK 前崩溃可恢复
```

就必须真的在 ACK 前退出。

这种叫 fault injection / fault testing。

---

# 20. 测试 Error Path，不要只测 Happy Path

一个创建接口至少会有：

```text
成功
非法 JSON
字段非法
未登录
无权限
资源冲突
依赖超时
数据库失败
重复请求
```

如果只有：

```text
200/201 happy path
```

测试价值很有限。

后端可靠性的很多关键知识都藏在 error path。

---

# 21. CI 在测试链中的角色

本地：

```text
“我机器上通过”
```

CI：

```text
每次提交在相对干净、重复的环境重新执行验证
```

常见：

```text
format
lint
unit test
integration/contract test
secret scan
build
```

CI 的意义不是“线上测试网站”。

它是自动化验证流水线的一部分。

部署是后面的 CD/发布阶段。

---

# 22. AI 生成的测试也必须审查

AI 很容易生成：

```text
大量测试函数
```

但可能：

- 断言过弱；
- mock 掉了真正风险；
- 没跑失败分支；
- 测试和实现共享同一个错误假设；
- 测试名字很专业，但根本没制造故障。

审查 AI 测试时问：

```text
如果我故意把关键不变量改坏，这个测试真的会红吗？
```

如果不会，它可能只是在制造绿色数字。

---

# 23. 代码审查应该优先找什么

比格式更重要：

```text
正确性
安全边界
事务边界
并发/重复副作用
错误处理
timeout/retry
资源泄漏
测试盲区
```

例如：

```text
少一个 tenant_id 条件
```

远比：

```text
变量名字不够优雅
```

严重。

---

# 24. Review 结论必须带触发场景

差的 review：

```text
这里可能有并发问题。
```

好的 review：

```text
两个请求同时读取 version=3 后都执行无 version 条件 UPDATE，后提交者会覆盖先提交者。当前测试只有顺序更新，因此挡不住。最小修复是 UPDATE 加 version 条件并断言 rows affected；再加并发/旧 version 测试。
```

这样才能验证问题是不是实际存在。

---

# 25. 测试通过以后还要问什么

```text
我证明了什么？
没有证明什么？
```

例如：

```text
Fake RAG test passed
```

只证明：

```text
本地 deterministic fake 下逻辑符合预期
```

不能写成：

```text
真实模型供应商已经生产验证
```

这种能力边界在工程汇报和面试里非常重要。

---

# 26. 本仓库练习

## 实验 1：让测试先失败

选择一个已有规则，例如：

```text
非 GET /healthz -> 405
```

故意删除 method check。

确认：

```text
测试变红
```

恢复后再绿。

如果始终绿，测试没有守住这条规则。

## 实验 2：写一个 Regression Test

从 `progress/debug-log.md` 里选一个真实 bug，先写复现测试，再修复。

## 实验 3：Fake 与 Integration 对比

同一个 Repository 行为：

```text
in-memory fake
vs
PostgreSQL integration
```

列出 fake 没有证明的三件事情。

## 实验 4：Fault Injection

模拟依赖：

```text
success
timeout
500
```

验证错误分类和重试策略。

---

# 27. Debug Log 模板

仓库已经有：

```text
progress/debug-log.md
```

至少保留：

```text
预期
实际
稳定复现
第一个错误状态
假设
验证假设的最小实验
根因
最小修复
回归证据
仍未覆盖的风险
```

真正重要的是“证据链”，不是日志写得长。

---

# 28. 常见误区

## 测试越多越好

错误。

没有明确不变量的大量脆弱测试会增加维护成本。

## Mock 越多越单元

错误。

过度 mock 可能只验证内部实现。

## Coverage 100% = 没 bug

错误。

Coverage 不判断断言质量。

## E2E 最真实，所以全部写 E2E

错误。

会变慢、难定位、易 flaky。

## Debug = 看最后一行报错

错误。

要找到数据/状态第一次偏离预期的位置。

## 测试绿了就 production-ready

错误。

还要看测试范围、运行环境、容量、依赖和运维边界。

---

# 29. 关闭文档复述

1. Unit、integration、contract、E2E 各自主要证明什么？
2. 为什么 in-memory Repository 不能证明 PostgreSQL transaction 正确？
3. Fake、stub、mock 的核心用途分别是什么？
4. 为什么测试内部函数调用次数容易导致脆弱？
5. Regression Test 应该怎样从一个真实 bug 产生？
6. Coverage 为什么不是质量分数？
7. Flaky Test 为什么不能简单靠 rerun 隐藏？
8. 为什么并发测试应该尽量等待事件而不是 `sleep` 猜时序？
9. 什么叫“第一个错误状态”？
10. Request ID 能解决什么，不能解决什么？
11. 为什么可靠性需要故障注入？
12. CI 和“线上测试”有什么区别？
13. AI 生成的测试最容易有什么假安全感？
14. 一个高质量 code review issue 为什么必须有触发场景和验证方法？

如果你能在遇到 bug 时先写出“预期、实际、复现、证据、假设”，而不是马上改代码，你的后端调试能力已经开始成型。
