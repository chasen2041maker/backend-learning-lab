-- 完成 challenges.sql 后再阅读。

SELECT id, title, status, priority, version, created_at
FROM tickets
WHERE tenant_id = 'tenant_demo'
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- 用实际上一页最后值替换参数。
SELECT id, title, status, priority, version, created_at
FROM tickets
WHERE tenant_id = $1
  AND (created_at, id) < ($2::timestamptz, $3::uuid)
ORDER BY created_at DESC, id DESC
LIMIT $4;

SELECT status, priority, count(*)
FROM tickets
WHERE tenant_id = 'tenant_demo'
GROUP BY status, priority
ORDER BY status, priority;

UPDATE tickets
SET status = 'closed', version = version + 1, updated_at = now()
WHERE id = $1 AND tenant_id = $2 AND version = $3 AND status = 'open'
RETURNING *;

SELECT id, payload
FROM outbox_events
WHERE published_at IS NULL AND next_attempt_at <= now()
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 20;
