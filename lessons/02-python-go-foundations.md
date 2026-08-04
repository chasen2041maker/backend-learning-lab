# 第 2 课：Python 与 Go 怎样表达同一个后端概念

## 数据模型

Python 通常用 Pydantic/dataclass 表达数据并在运行时验证；Go 用 struct 和编译器类型检查。

Python：

```python
from pydantic import BaseModel, Field

class TicketCreate(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
```

Go：

```go
type CreateTicketInput struct {
    TenantID string `json:"tenant_id"`
    Title    string `json:"title"`
}
```

Go 的 struct tag 只告诉 JSON 解码字段名，不自动完成长度验证；业务仍需显式校验。

## 错误

Python 使用异常传播失败：

```python
ticket = await repository.get(ticket_id)
if ticket is None:
    raise TicketNotFound(ticket_id)
```

Go 把错误作为返回值：

```go
ticket, err := repo.Get(ctx, ticketID)
if err != nil {
    return Ticket{}, fmt.Errorf("get ticket: %w", err)
}
```

两者都必须保留错误上下文，不能悄悄吞掉异常。

## 接口和依赖反转

Service 依赖 Repository 接口，而不是直接依赖某个数据库实现。这样单元测试可以使用内存实现，生产再换 PostgreSQL。

这不是为了“看起来高级”，而是为了让业务规则能被快速、确定性测试。

## Context 与取消

Go 的 `context.Context` 携带 deadline、取消信号和请求范围元数据；Python 常用 `asyncio.timeout`、任务取消和显式参数实现类似边界。

不要把 Context 当成随意存放业务参数的全局字典。

## 练习

在两个示例项目中同时新增：

- `priority`：只能是 `low/normal/high`；
- 创建时默认 `normal`；
- 非法值返回 400；
- 单元测试覆盖默认值和非法值。
