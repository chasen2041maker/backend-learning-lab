# 第 2 课三级提示

## 提示 1

priority 同时出现在外部输入 `TicketCreate` 和内部状态 `Ticket`。先让第一个默认值测试
通过，再处理非法值。

## 提示 2

Python 的 `Literal` 可以声明有限字符串集合。`Ticket.new()` 负责把已经验证的命令转换为
内部状态，因此需要从 `command` 复制该字段。

## 提示 3

检查三处：`typing` 导入、`TicketCreate` 字段、`Ticket` 字段和 `Ticket.new()` 构造参数。
不需要修改 Service、Repository 或测试。
