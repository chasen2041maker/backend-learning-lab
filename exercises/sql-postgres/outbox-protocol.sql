-- Transactional Outbox publisher protocol (PostgreSQL).
-- Parameters use :name notation so the learner can translate them to a driver.

-- 1. Claim a bounded batch in one short transaction. Do not keep the transaction
-- open while publishing to Redis.
WITH candidates AS (
    SELECT id
    FROM outbox_events
    WHERE published_at IS NULL
      AND dead_lettered_at IS NULL
      AND next_attempt_at <= now()
      AND (locked_until IS NULL OR locked_until < now())
    ORDER BY next_attempt_at, created_at
    FOR UPDATE SKIP LOCKED
    LIMIT :batch_size
)
UPDATE outbox_events AS event
SET locked_by = :worker_id,
    locked_until = now() + interval '30 seconds',
    lease_token = lease_token + 1
FROM candidates
WHERE event.id = candidates.id
RETURNING event.*;

-- 2a. Mark success only while this worker still owns the lease. A row count of
-- zero means the lease was reclaimed and this stale worker is fenced out.
UPDATE outbox_events
SET published_at = now(),
    locked_by = NULL,
    locked_until = NULL,
    last_error = NULL
WHERE id = :event_id
  AND locked_by = :worker_id
  AND lease_token = :lease_token
  AND published_at IS NULL
  AND dead_lettered_at IS NULL;

-- 2b. On failure, increment attempts and apply capped exponential backoff.
-- Sanitize error text before storage; never persist credentials or payload secrets.
UPDATE outbox_events
SET attempts = attempts + 1,
    next_attempt_at = now()
        + make_interval(secs => LEAST(300, power(2, LEAST(attempts, 8))::integer)),
    last_error = left(:sanitized_error, 500),
    dead_lettered_at = CASE WHEN attempts + 1 >= 8 THEN now() END,
    locked_by = NULL,
    locked_until = NULL
WHERE id = :event_id
  AND locked_by = :worker_id
  AND lease_token = :lease_token
  AND published_at IS NULL
  AND dead_lettered_at IS NULL;

-- Delivery is at-least-once: publishing may succeed and the success UPDATE may
-- fail. Keep outbox id as event_id and require consumer event_id idempotency.
