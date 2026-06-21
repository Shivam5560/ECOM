CREATE TABLE IF NOT EXISTS workflow_tasks (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    service TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT NOT NULL,
    inputs JSONB NOT NULL DEFAULT '[]'::jsonb,
    outputs JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO workflow_tasks (code, name, service, status, description, inputs, outputs)
VALUES
    ('test-inventory-reservation', 'Test inventory reservation', 'product-service', 'ready', 'Test task for inventory reservation.', '["correlation_id","order_id"]'::jsonb, '["inventory.reserved"]'::jsonb),
    ('test-checkout-confirmation', 'Test checkout confirmation', 'notification-service', 'ready', 'Test task for checkout confirmation.', '["correlation_id","order_id"]'::jsonb, '["order.confirmed"]'::jsonb)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    service = EXCLUDED.service,
    status = EXCLUDED.status,
    description = EXCLUDED.description,
    inputs = EXCLUDED.inputs,
    outputs = EXCLUDED.outputs,
    updated_at = now();
