INSERT INTO tenants (id, name)
VALUES ('tenant_demo', 'Demo Tenant'), ('tenant_other', 'Other Tenant')
ON CONFLICT (id) DO NOTHING;

INSERT INTO tickets (tenant_id, title, priority, created_at)
SELECT
    'tenant_demo',
    'Learning ticket ' || number,
    CASE WHEN number % 3 = 0 THEN 'high' WHEN number % 3 = 1 THEN 'normal' ELSE 'low' END,
    now() - (number || ' minutes')::interval
FROM generate_series(1, 50) AS number;

INSERT INTO tickets (tenant_id, title)
VALUES ('tenant_other', 'This row must not appear in tenant_demo queries');
