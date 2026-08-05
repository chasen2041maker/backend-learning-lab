# 第 3 课三级提示

## 提示 1

先 `await self._repository.get(tenant_id, ticket_id)`。`None` 同时覆盖不存在和跨租户隐藏；
它与状态冲突是两种不同失败。

## 提示 2

检查顺序：不存在、已经 closed、expected_version 不等于当前 version。错误使用文件中已定义的
三个异常类。

## 提示 3

成功路径复制 ticket 字典，设置 `status="closed"`，version 加一，然后
await `save(tenant_id, ticket_id, ticket)` 并返回。
Service 不导入 `api.py`，也不返回 `status=409`。
