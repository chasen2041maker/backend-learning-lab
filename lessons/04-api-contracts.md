# 第 4 课：用真实契约守住输入、身份与租户边界

预计用时：70～90 分钟。实验数量：4 个主实验、2 个故障实验、3 个失败测试。

## 你将亲手完成什么

- 读取 `contracts/http-cases.json`，区分描述文档与机器验收；
- 证明 JSON 语法错误是 400，字段/类型/业务约束错误是 422；
- 证明 Token 产生可信 Principal，客户端 `tenant_id` 会被拒绝；
- 创建 tenant A 的工单，用 tenant B 查询并观察统一 404；
- 运行 Python 的共享契约测试，并解释它如何防止实现漂移；
- 用失败测试完成一个契约查询函数，不修改契约来迎合代码。

本课只运行 Python。第 9 周会让 Go 读取同一份 JSON 用例，复现你已经理解的边界。

## 本课不讲什么

本课不修改契约语义，不实现 Go，不接数据库，也不展开事件契约。只观察现有 HTTP 机器用例如何
约束 Python 实现。

## 前置条件与当前状态

你已完成第 1～3 课，知道 Handler、Service、Repository 的边界。当前契约有两种形式：

- [api-contract.md](../contracts/api-contract.md)：给人阅读的语义与示例；
- [http-cases.json](../contracts/http-cases.json)：Python/Go 都能读取的关键行为用例。

先验证机器文件可解析：

```powershell
python -m json.tool contracts/http-cases.json > $null
python scripts/validate_contracts.py
```

关键输出：

```text
contracts valid: 12 HTTP cases, 8 event fields
```

第二个数字来自同一校验脚本检查的事件 envelope；本课只学习 HTTP 部分。

### 逐字段读一个机器用例

`http-cases.json` 顶层的 `contract_version` 标记契约格式版本，`id_format` 规定 ID 必须是
UUID v4 文本，`title_length_unit` 规定长度按 Unicode code point 计算。每个 section 对应一个
API 行为族，例如 `create_cases`、`get_cases` 和 `close_cases`。

单个 case 中：

- `name` 是可读的用例标识，不参与业务判断；
- `authorization` 决定测试是否发送教学 Token；
- `body` 或 `raw_body` 是输入，后者用于表达无法表示成正常 JSON 值的字节；
- `seed_tenant` 与 `request_tenant` 描述跨租户前置状态；
- `expected_status` 是 HTTP 状态码；
- `expected_code` 才是客户端可稳定分支的机器码。

`message` 不在机器契约中，因为它用于给人阅读，可以改措辞或本地化。客户端若根据
“ticket does not exist”这样的句子分支，文案修改就会破坏程序；应使用 `expected_code`
对应的响应 `code`。

## 实验 1：从机器契约找输入边界

```powershell
python -c "import json; from pathlib import Path; c=json.loads(Path('contracts/http-cases.json').read_text(encoding='utf-8')); print([(x['name'], x['expected_status'], x['expected_code']) for x in c['create_cases']])"
```

输出会列出 12 个创建用例。重点对照：

| 用例 | JSON 能解析吗 | 结果 |
| --- | --- | --- |
| empty body | 否，没有完整 JSON 值 | `400 invalid_json` |
| malformed json | 否，语法被截断 | `400 invalid_json` |
| trailing json | 否，一个 Body 有两个值 | `400 invalid_json` |
| numeric title | 是，但字段类型错误 | `422 invalid_ticket_input` |
| unknown field | 是，但模型禁止额外字段 | `422 invalid_ticket_input` |
| client tenant forgery | 是，但 tenant_id 不允许由客户端提交 | `422 invalid_ticket_input` |

strict JSON 不只是“能被 JSON parser 读取”。它还包含顶层对象、字段集合和精确类型规则。

单独执行 strict JSON 与 Unicode 实验：

```powershell
cd exercises\python-ticket-api
python -m pytest tests/test_tickets.py -k "contract_rejects_unknown_fields" -v -p no:cacheprovider
```

预计 `1 passed`。测试先提交额外字段并断言 422，再提交 100 个中文字符并断言 201。

## 实验 2：可信 Principal 从哪里来

打开 [main.py](../exercises/python-ticket-api/app/main.py)，找到 `LAB_TOKENS` 与 `get_principal`。

```text
Authorization Header
-> get_principal 验证 Bearer token
-> 服务端构造 Principal(subject, tenant_id)
-> Handler 把 principal.tenant_id 传给 Service
```

教学 Token 是本地桩，不是生产 JWT。关键边界是：只有通过服务端验证的凭据才能产生 Principal；
JSON Body、Query 和 Path 中的 `tenant_id` 都不可信。

运行相关测试：

```powershell
cd exercises\python-ticket-api
python -m pytest tests/test_tickets.py -k "authentication_and_client_tenant_forgery" -v -p no:cacheprovider
```

预计：`1 passed`。一个测试函数内部同时证明缺 Token 返回 401、伪造 tenant_id 返回 422。

### 故障实验：把 tenant_id 加回输入模型会怎样

不要修改成品代码。只写出后果：持有 tenant A Token 的客户端可以在 Body 声称自己属于 tenant B；
如果 Service 相信 Body，认证就失去意义。可信身份必须覆盖客户端声明，而不是与其“二选一”。

## 实验 3：跨租户为什么返回 404

启动服务：

```powershell
cd exercises\python-ticket-api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另一个窗口创建 tenant A 工单，并让 PowerShell 解析响应：

```powershell
$created = curl.exe -sS `
  -X POST http://127.0.0.1:8000/api/v1/tickets `
  -H "Authorization: Bearer lab-token-tenant-a" `
  -H "Content-Type: application/json" `
  --data-raw '{\"title\":\"Private-ticket\"}' | ConvertFrom-Json
$ticketId = $created.data.id
$ticketId
```

再用 tenant B Token 查询：

```powershell
curl.exe -sS -i `
  -H "Authorization: Bearer lab-token-tenant-b" `
  "http://127.0.0.1:8000/api/v1/tickets/$ticketId"
```

关键结果：

```text
HTTP/1.1 404 Not Found
"code":"ticket_not_found"
```

服务不返回 403，因为 403 会告诉 tenant B“这个 ID 确实存在，只是你无权访问”。按 tenant 查询后统一
返回 404，隐藏资源存在性。当前内存 Repository 与未来数据库查询都必须把 `tenant_id` 放入边界。

停止 Uvicorn。

## 实验 4：同一份用例如何驱动 Python

运行 Python 的共享契约测试：

```powershell
cd exercises\python-ticket-api
python -m pytest tests/test_tickets.py -k shared -v -p no:cacheprovider
```

关键结果：5 个 shared 测试函数通过，分别读取 create、health、get、list、close 用例。测试不是把
所有期望重新抄一遍，而是运行时打开仓库根目录的 `contracts/http-cases.json`。

关注两个例子：

- `padded 200 character title`：先 trim，再按 Unicode 字符数检查；
- `uuid v1 ticket id` 与 `compact uuid ticket id`：只接受约定文本形式的 RFC 4122 UUID v4。

单独执行 UUID v4 实验：

```powershell
python -m pytest tests/test_tickets.py -k shared_get -v -p no:cacheprovider
```

预计 `1 passed`。该测试逐项运行普通缺失 UUID、跨租户 ID、UUID v1 和无连字符 UUID，
并按契约核对 404 或 422。

### 故障实验：只改代码不改契约

这个实验必须在自己的临时学习分支进行，完成后恢复代码。打开
`exercises/python-ticket-api/app/models.py`，把 `StrictInput` 的
`ConfigDict(extra="forbid", strict=True)` 临时改为 `extra="ignore"`，再运行：

```powershell
cd exercises\python-ticket-api
python -m pytest tests/test_tickets.py -k shared_create -v -p no:cacheprovider
```

`unknown field` 和 `client tenant forgery` 会从契约要求的 `422` 漂移成 `201`，测试输出中的
关键失败是 `assert response.status_code == case["expected_status"]`。把实现恢复为
`extra="forbid"`，再次运行同一命令，预计 `1 passed`。这就是一次完整的
“制造漂移 -> 看见失败 -> 修复实现 -> 再次通过”，无需修改契约来迎合错误实现。

## 引导练习：让契约自己回答问题

打开 [第 4 课实验](../exercises/04-api-contracts/README.md)，先运行：

```powershell
python -m pytest exercises/04-api-contracts/tests -v -p no:cacheprovider
```

预计 3 个 `NotImplementedError`。只修改 `starter/contract_reader.py`，实现按 section 与
`expected_code` 返回用例名。限制：

- 不硬编码用例名称；
- 不排序，保持契约原顺序；
- section 不是 list 时显式报错；
- 不修改 `http-cases.json` 或测试。

需要时使用[三级提示](../exercises/04-api-contracts/hints.md)。完成后预计 `3 passed`。

## 独立练习

从契约中另外找出并记录：

1. 两个 UUID 格式失败用例；
2. 三个 expected_version 类型失败用例；
3. 跨租户 404 用例；
4. list limit 的边界用例。

每条记录必须写出 section、name、expected_status、expected_code，不能只写自然语言。

## 常见错误与排查

1. 从错误目录运行 pytest：看报错中的 `rootdir` 与契约路径。
2. 把 `400` 和 `422` 混为一谈：先问 JSON parser 是否得到一个完整值。
3. 用 Body tenant_id 做过滤：身份来源错误，必须使用 Principal。
4. 跨租户返回 403：泄露资源存在性，与当前契约不符。
5. UUID 能被某个库解析就接受：契约还限制版本与规范文本格式。
6. 测试写死当前用例名：没有真正读取共享契约。

## 不看代码复述

1. Markdown 契约与 JSON 用例分别服务谁？
2. `invalid_json` 和 `invalid_ticket_input` 的分界在哪里？
3. Principal 为什么可信，Body tenant_id 为什么不可信？
4. 跨租户读取为什么统一 404？
5. Python 共享测试如何证明它真的读取同一份 JSON？
6. 哪些 API 变化可能破坏现有客户端？

## 本课总结与下一课

第 0～4 周的 Python 样板到这里结束：先观察网络，再理解模型，然后用失败测试抽边界，最后用共享
契约守住外部行为。第 5 周才启动 Docker 与本地依赖；第 8 周学习 Go 语言基础，第 9 周用 Go
`net/http` 读取同一份契约。不要现在同时改 Python 与 Go。
