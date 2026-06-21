CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total INTEGER NOT NULL DEFAULT 0,
    lines JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by TEXT,
    updated_by TEXT,
    deleted_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO orders (id, user_id, status, total, lines, created_by, updated_by, deleted_at, is_active)
VALUES
    ('test-ord-1001', 'buyer-1', 'confirmed', 249, '[{"product_id":"test-aurora-speaker","name":"Test Aurora Speaker","quantity":1,"unit_price":249}]'::jsonb, 'buyer-1', 'workflow-service', NULL, TRUE)
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status,
    total = EXCLUDED.total,
    lines = EXCLUDED.lines,
    updated_at = now(),
    deleted_at = NULL,
    is_active = TRUE;
