-- 1. 查询 tenant_demo 最新 20 个工单，只返回必要字段。
-- TODO

-- 2. 使用上一页最后一条的 created_at 和 id 完成下一页游标查询。
-- TODO

-- 3. 统计 tenant_demo 每种 status/priority 的数量。
-- TODO

-- 4. 使用 expected_version 乐观关闭工单。检查影响行数。
-- TODO

-- 5. 用一个事务完成：记录 webhook、关闭工单、插入 ticket.closed outbox。
-- 重复 provider_event_id 必须安全识别，不重复应用状态变化。
-- TODO

-- 6. 使用 FOR UPDATE SKIP LOCKED 领取最多 20 个未发布 Outbox。
-- TODO
