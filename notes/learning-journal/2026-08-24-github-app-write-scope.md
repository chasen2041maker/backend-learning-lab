# 2026-08-24：为什么“我有仓库权限”仍然可能无法写入——GitHub App 授权层级

这次不是后端业务代码问题，而是一次很典型的“**身份权限看起来都对，但集成写操作仍然 403**”的排查。

它值得保留，因为这个问题以后在 GitHub App、CI Bot、自动化 Agent、企业集成里都会再次出现。

---

## 当时最容易形成的错误理解

一开始很容易认为：

```text
我已经登录 GitHub
+
ChatGPT 显示已连接
+
仓库页面显示我有 admin/push
=
这个集成一定可以写仓库
```

实际上不成立。

关键原因是：**人的仓库权限、产品侧允许 AI 执行动作、GitHub App 自己的安装范围，是不同授权层。**

---

## 正确的权限模型

可以按下面几层理解：

```text
1. 产品侧动作权限
   ChatGPT 是否被允许执行 write action？

2. GitHub 用户身份
   当前认证用户是谁？

3. GitHub App 安装账户
   App 是否安装在目标 User / Organization 上？

4. Repository installation scope
   目标仓库是否包含在这次 App installation 的仓库范围里？

5. App permission
   这次 installation 是否拥有 Contents write / PR write 等所需权限？

6. Repository policy
   branch protection / ruleset / required checks 是否进一步限制写入？
```

任何一层不满足，都可能出现：

```text
读得到
但写不了
```

---

## 为什么“能读公开仓库”不能证明写权限

公开仓库本来就允许匿名或低权限读取很多信息。

所以：

```text
GET repository
GET file
GET branch
```

成功，只能证明：

> 当前请求有读取这个资源的能力。

它不能证明：

```text
create blob
update file
create commit
move branch ref
```

也被允许。

这是权限排查里非常重要的原则：

> **Read success is not write evidence.**

---

## 为什么仓库 metadata 显示 push/admin 也可能仍然写失败

另一个容易误判的地方是：

```text
repository.permissions.push = true
repository.permissions.admin = true
```

这通常说明“当前用户”本身对仓库有这些能力。

但真正执行自动化写操作时，GitHub 可能使用的是：

```text
GitHub App installation token
```

这个 token 的可访问资源由 App installation 决定。

因此可能出现：

```text
用户本人：可以 push
GitHub App：没有安装到这个 owner/repo
结果：integration write 403
```

所以排权限时必须问：

> **到底是谁的 token 在执行这次写操作？**

不能只看网页登录账号有没有权限。

---

## `Resource not accessible by integration` 提示了什么

这类 403 很有价值，因为它通常指向：

```text
integration / app installation / resource scope
```

而不是：

```text
Markdown 内容写错了
Git commit message 不合法
代码语法错误
```

排查时不要因为连续写失败就反复修改文件内容。

先验证授权路径。

---

## 一条更可靠的排查顺序

以后遇到“第三方集成能读不能写”，按这个顺序：

### 1. 确认执行身份

```text
当前 GitHub user 是谁？
```

避免登录到了另一个账号。

### 2. 确认 App 安装在哪些账户/组织

目标仓库如果属于：

```text
owner = account_A
```

但 App 只安装在：

```text
account_B
```

就算你同时拥有 A/B 两个账号，也不代表 App 能写 A 的仓库。

### 3. 确认目标 repo 被 installation 选中

GitHub App 可以配置：

```text
All repositories
```

或者：

```text
Only selected repositories
```

后者如果没选目标仓库，仍然 403。

### 4. 确认需要的具体权限

例如：

```text
读 issue
```

和：

```text
写 repository contents
```

不是同一个 permission。

### 5. 再检查 branch protection / ruleset

如果 App 已有 contents write，但：

```text
main 禁止直接 push
必须 PR
必须签名 commit
必须通过 checks
```

也可能无法直接更新 branch。

### 6. 用最小写操作验证

权限链确认后，再尝试最小变更。

如果能：

```text
create blob
create tree
create commit
update ref
```

就证明 Git 写路径真正打通。

### 7. 写完以后必须验证远端

不要把：

```text
API 返回 success
```

当成最终证据。

还应该确认：

```text
main head 是否前移
compare 是否 ahead_by=1
变更文件是否符合预期
CI/status 是否出现失败
```

---

## 这和后端 Authentication / Authorization 有什么关系

本质上还是前面认证课的同一套原则：

```text
Authentication
= 你是谁？

Authorization
= 这个身份在这个资源上能做什么？
```

但 GitHub App 又多了一层：

```text
user identity
!=
integration identity
```

例如：

```text
Human user: Yong
有 repo admin

Automation: GitHub App installation
只有 repo read
```

两个 Principal 不一样，权限也不一样。

这和后端服务里：

```text
最终用户 Principal
```

以及：

```text
service/workload identity
```

必须分开，是同一个工程思想。

---

## 和微服务身份传播的连接

以后在服务间调用里也会遇到类似错误：

```text
Alice 有权限操作订单
```

不等于：

```text
任意一个拿到 Alice user_id 的内部服务都自动获得这个权限
```

仍然要分：

```text
User Principal
Service Identity
Resource Authorization
```

GitHub App 的问题只是一个非常具体的现实例子。

---

## 不应该长期保存什么

这次没有把某个版本 ChatGPT UI 的具体按钮位置写成长期知识。

因为：

```text
Settings 在哪里
按钮叫 Connect 还是 Configure
```

产品 UI 会变化。

真正值得保留的是：

```text
产品侧动作权限
!= 用户权限
!= App installation scope
!= repository contents permission
```

这才是跨产品都成立的心智模型。

---

## 我现在应该能回答

关闭文档后，应该能解释：

1. 为什么公开仓库能读不代表能写？
2. 为什么用户本人有 admin 仍可能出现 integration 403？
3. GitHub 用户身份和 GitHub App installation identity 有什么区别？
4. `Only selected repositories` 为什么会造成某个 repo 特别写不了？
5. Contents write 和 PR/Issue 权限为什么要分开？
6. 为什么排权限时要先确认“到底谁的 token 在执行”？
7. branch protection 属于哪一层限制？
8. 写操作成功后为什么还要重新检查 branch/compare/CI？

如果这些能讲清楚，以后遇到 CI Bot、GitHub App、自动化 Agent 的权限问题，就不会只盯着“我这个账号明明是管理员”。
