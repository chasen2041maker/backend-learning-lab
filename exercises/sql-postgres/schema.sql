CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tenants (
    id text PRIMARY KEY,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tickets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id text NOT NULL REFERENCES tenants(id),
    title text NOT NULL CHECK (
        title = btrim(title)
        AND length(title) BETWEEN 1 AND 200
    ),
    status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    priority text NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    version bigint NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tickets_tenant_created
    ON tickets (tenant_id, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_tickets_tenant_status_created
    ON tickets (tenant_id, status, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS idempotency_records (
    tenant_id text NOT NULL REFERENCES tenants(id),
    operation text NOT NULL,
    idempotency_key text NOT NULL,
    request_hash text NOT NULL,
    response_status integer,
    response_body jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, operation, idempotency_key)
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider text NOT NULL,
    provider_event_id text NOT NULL,
    tenant_id text NOT NULL REFERENCES tenants(id),
    sequence_no bigint,
    payload_sha256 text NOT NULL,
    status text NOT NULL CHECK (status IN ('received', 'applied', 'rejected')),
    received_at timestamptz NOT NULL DEFAULT now(),
    applied_at timestamptz,
    UNIQUE (provider, provider_event_id)
);

CREATE TABLE IF NOT EXISTS outbox_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    event_type text NOT NULL,
    event_version integer NOT NULL DEFAULT 1 CHECK (event_version > 0),
    payload jsonb NOT NULL,
    request_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    last_error text,
    locked_by text,
    locked_until timestamptz,
    lease_token bigint NOT NULL DEFAULT 0 CHECK (lease_token >= 0),
    dead_lettered_at timestamptz,
    CHECK (published_at IS NULL OR dead_lettered_at IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_outbox_unpublished
    ON outbox_events (next_attempt_at, created_at)
    WHERE published_at IS NULL AND dead_lettered_at IS NULL;

CREATE TABLE IF NOT EXISTS processed_events (
    consumer_name text NOT NULL,
    event_id uuid NOT NULL,
    processed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (consumer_name, event_id)
);
