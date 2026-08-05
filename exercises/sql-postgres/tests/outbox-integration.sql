\set ON_ERROR_STOP on

BEGIN;

DELETE FROM outbox_events
WHERE id = '00000000-0000-4000-8000-000000000099';

INSERT INTO outbox_events (
    id,
    aggregate_type,
    aggregate_id,
    event_type,
    event_version,
    payload
) VALUES (
    '00000000-0000-4000-8000-000000000099',
    'ticket',
    '00000000-0000-4000-8000-000000000001',
    'ticket.closed',
    1,
    '{"ticket_id":"00000000-0000-4000-8000-000000000001","status":"closed","version":2}'
);

UPDATE outbox_events
SET locked_by = 'worker-a',
    locked_until = now() + interval '30 seconds',
    lease_token = lease_token + 1
WHERE id = '00000000-0000-4000-8000-000000000099'
  AND published_at IS NULL
  AND dead_lettered_at IS NULL
  AND next_attempt_at <= now()
  AND (locked_until IS NULL OR locked_until < now());

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM outbox_events
        WHERE id = '00000000-0000-4000-8000-000000000099'
          AND locked_by = 'worker-a'
          AND lease_token = 1
    ) THEN
        RAISE EXCEPTION 'worker-a did not claim the event';
    END IF;
END $$;

UPDATE outbox_events
SET locked_until = now() - interval '1 second'
WHERE id = '00000000-0000-4000-8000-000000000099';

UPDATE outbox_events
SET locked_by = 'worker-b',
    locked_until = now() + interval '30 seconds',
    lease_token = lease_token + 1
WHERE id = '00000000-0000-4000-8000-000000000099'
  AND published_at IS NULL
  AND dead_lettered_at IS NULL
  AND next_attempt_at <= now()
  AND locked_until < now();

DO $$
DECLARE
    affected integer;
BEGIN
    UPDATE outbox_events
    SET published_at = now()
    WHERE id = '00000000-0000-4000-8000-000000000099'
      AND locked_by = 'worker-a'
      AND lease_token = 1;
    GET DIAGNOSTICS affected = ROW_COUNT;
    IF affected <> 0 THEN
        RAISE EXCEPTION 'stale worker-a was not fenced';
    END IF;
END $$;

DO $$
DECLARE
    attempt_number integer;
    affected integer;
BEGIN
    FOR attempt_number IN 1..8 LOOP
        UPDATE outbox_events
        SET attempts = attempts + 1,
            next_attempt_at = now()
                + make_interval(secs => LEAST(300, power(2, LEAST(attempts, 8))::integer)),
            last_error = 'simulated publish failure',
            dead_lettered_at = CASE WHEN attempts + 1 >= 8 THEN now() END,
            locked_by = NULL,
            locked_until = NULL
        WHERE id = '00000000-0000-4000-8000-000000000099'
          AND locked_by = CASE WHEN attempt_number = 1 THEN 'worker-b' ELSE 'worker-retry' END
          AND published_at IS NULL
          AND dead_lettered_at IS NULL;
        GET DIAGNOSTICS affected = ROW_COUNT;
        IF affected <> 1 THEN
            RAISE EXCEPTION 'failure update % affected % rows', attempt_number, affected;
        END IF;

        EXIT WHEN attempt_number = 8;

        UPDATE outbox_events
        SET next_attempt_at = now(),
            locked_by = 'worker-retry',
            locked_until = now() + interval '30 seconds',
            lease_token = lease_token + 1
        WHERE id = '00000000-0000-4000-8000-000000000099'
          AND published_at IS NULL
          AND dead_lettered_at IS NULL;
    END LOOP;

    IF NOT EXISTS (
        SELECT 1 FROM outbox_events
        WHERE id = '00000000-0000-4000-8000-000000000099'
          AND attempts = 8
          AND dead_lettered_at IS NOT NULL
          AND published_at IS NULL
    ) THEN
        RAISE EXCEPTION 'event did not enter DLQ state on attempt 8';
    END IF;
END $$;

ROLLBACK;

SELECT 'outbox integration passed' AS result;
