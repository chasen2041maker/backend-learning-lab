# Contracts：把“我们约定这样工作”变成可验证行为

`contracts/` 保存的是系统边界，不是实现细节。

一个 API 或事件契约存在的意义是：

> Python、Go、客户端、测试和未来重构都不能各自凭感觉解释同一个行为。

---

## HTTP 契约

### [`api-contract.md`](api-contract.md)

给人阅读的语义说明，包括：

- 身份与租户边界；
- Method / Path / Body；
- 成功与错误行为；
- stable machine-readable error code；
- request ID；
- 输入规则。

### [`http-cases.json`](http-cases.json)

机器可读的关键行为用例。

Python 和 Go 都应该读取同一份用例，避免出现：

```text
Python 接受某个输入
Go 拒绝同一个输入
```

却没人知道哪个才是契约。

---

## Event 契约

### [`event-contract.md`](event-contract.md)

给人阅读的事件语义：Envelope、版本、幂等、ACK、tenant、trace 等。

### [`event.schema.json`](event.schema.json)

机器校验事件 Envelope 的结构。

事件契约不只是“JSON 长什么样”，还包含：

```text
重复怎么办？
未知版本怎么办？
什么时候 ACK？
旧事件能不能覆盖新状态？
```

---

## 人类文档和机器契约为什么都需要

只有 Markdown：

```text
人看懂了
但实现可能悄悄漂移
```

只有 JSON Schema / cases：

```text
机器能检查
但人不知道为什么这样设计
```

所以仓库同时保留：

```text
Human-readable semantics
+
Machine-executable evidence
```

---

## 修改契约的正确顺序

不要先改实现，再把测试改到通过。

推荐：

```text
1. 先说明为什么行为要变
2. 判断是不是 breaking change
3. 修改人类契约
4. 修改/新增机器 case 或 schema
5. 让现有实现失败
6. 修改 Python / Go 实现
7. 运行 contract tests
8. 检查旧客户端/旧事件兼容性
```

如果你为了让错误实现通过而删除 failing case，契约就失去意义。

---

## Authentication 相关特别说明

仓库里的固定教学 Token 只用于证明：

```text
credential
↓ server validation
Principal(subject, tenant)
```

这个信任边界。

它们不是生产 JWT，也不应该被扩展成“把字符串写死就是登录系统”。真实认证机制见 [`../lessons/10-auth-security.md`](../lessons/10-auth-security.md)。

---

## 兼容性怎么想

通常更安全的演进：

```text
新增可选字段
→ 老消费者仍能工作
```

通常更危险：

```text
删除字段
改变字段语义
改变错误码含义
复用旧事件字段编号/版本语义
```

具体是否 breaking 取决于真实客户端和契约承诺，不要只靠“JSON 还能 parse”判断。

---

## 验证

仓库根目录：

```powershell
python scripts/validate_contracts.py
```

完整检查：

```powershell
powershell -File scripts/check.ps1
```

自动检查通过只能证明当前已编码的规则一致，不证明契约本身的业务设计一定正确。设计仍需要失败场景和人工审查。
