\connect ecom

SET search_path TO auth;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO users (id, email, password_hash, roles, is_active)
VALUES
    ('admin-1', 'admin@ecom.dev', '$2b$12$sPsr/nn3x5M7aonP4oMqzeiMQu.D8KTdp9ihwr3fSxTUDwToD1sTe', '["admin"]'::jsonb, TRUE),
    ('buyer-1', 'buyer@ecom.dev', '$2b$12$Pn5KZMDJ8vrMgF86wc7Q1.byFB4xZbxe..VuF30/miY4ECaW8VbS6', '["customer"]'::jsonb, TRUE)
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    roles = EXCLUDED.roles,
    is_active = EXCLUDED.is_active;

SET search_path TO users;

CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY,
    auth_subject TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT,
    phone TEXT,
    address JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

INSERT INTO user_profiles (id, auth_subject, email, display_name, password_hash, phone, address)
VALUES
    ('admin-profile', 'admin-1', 'admin@ecom.dev', 'Catalog Admin', '$2b$12$sPsr/nn3x5M7aonP4oMqzeiMQu.D8KTdp9ihwr3fSxTUDwToD1sTe', '+91-90000-00001', '{"city":"Bengaluru","country":"IN"}'::jsonb),
    ('buyer-profile', 'buyer-1', 'buyer@ecom.dev', 'Demo Buyer', '$2b$12$Pn5KZMDJ8vrMgF86wc7Q1.byFB4xZbxe..VuF30/miY4ECaW8VbS6', '+91-90000-00002', '{"city":"Mumbai","country":"IN"}'::jsonb)
ON CONFLICT (id) DO UPDATE SET
    auth_subject = EXCLUDED.auth_subject,
    email = EXCLUDED.email,
    display_name = EXCLUDED.display_name,
    password_hash = EXCLUDED.password_hash,
    phone = EXCLUDED.phone,
    address = EXCLUDED.address,
    updated_at = now(),
    deleted_at = NULL;

SET search_path TO products;

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price INTEGER NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    rating DOUBLE PRECISION NOT NULL DEFAULT 4.5,
    image TEXT NOT NULL DEFAULT '',
    accent TEXT NOT NULL DEFAULT '#0e5d4e',
    created_by TEXT,
    updated_by TEXT,
    deleted_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO products (id, name, category, description, price, stock, rating, image, accent, created_by, updated_by, deleted_at, is_active)
VALUES
    ('aurora-speaker', 'Aurora Speaker', 'Audio', 'Portable room speaker with balanced sound and woven grille.', 249, 8, 4.8, 'https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=900&q=80', '#0e5d4e', 'admin-1', 'admin-1', NULL, TRUE),
    ('linea-tote', 'Linea Carry Tote', 'Carry', 'Structured recycled-canvas tote for everyday travel.', 188, 5, 4.7, 'https://images.unsplash.com/photo-1594223274512-ad4803739b7c?auto=format&fit=crop&w=900&q=80', '#b08a45', 'admin-1', 'admin-1', NULL, TRUE),
    ('halo-lamp', 'Halo Task Lamp', 'Desk', 'Dimmable aluminum desk lamp with warm and focused light.', 164, 11, 4.6, 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80', '#4f6f8f', 'admin-1', 'admin-1', NULL, TRUE),
    ('terra-planter', 'Terra Self-Watering Planter', 'Home', 'Ceramic planter with a hidden water reservoir and brass indicator.', 72, 14, 4.5, 'https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=900&q=80', '#557153', 'admin-1', 'admin-1', NULL, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    stock = EXCLUDED.stock,
    rating = EXCLUDED.rating,
    image = EXCLUDED.image,
    accent = EXCLUDED.accent,
    updated_by = EXCLUDED.updated_by,
    updated_at = now(),
    deleted_at = NULL,
    is_active = TRUE;

SET search_path TO orders;

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
    ('ord-demo-1001', 'buyer-1', 'confirmed', 437, '[{"product_id":"aurora-speaker","name":"Aurora Speaker","quantity":1,"unit_price":249},{"product_id":"linea-tote","name":"Linea Carry Tote","quantity":1,"unit_price":188}]'::jsonb, 'buyer-1', 'workflow-service', NULL, TRUE)
ON CONFLICT (id) DO UPDATE SET
    user_id = EXCLUDED.user_id,
    status = EXCLUDED.status,
    total = EXCLUDED.total,
    lines = EXCLUDED.lines,
    updated_by = EXCLUDED.updated_by,
    updated_at = now(),
    deleted_at = NULL,
    is_active = TRUE;

SET search_path TO workflow;

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
    ('inventory-reservation', 'Inventory reservation', 'product-service', 'ready', 'Reserve stock before confirming payment.', '["correlation_id","order_id","lines"]'::jsonb, '["inventory.reserved","inventory.rejected"]'::jsonb),
    ('payment-authorization', 'Payment authorization', 'payment-service', 'ready', 'Authorize COD or future gateway payment before confirmation.', '["correlation_id","order_id","total","mode"]'::jsonb, '["payment.authorized","payment.failed"]'::jsonb),
    ('checkout-confirmation', 'Checkout confirmation', 'notification-service', 'ready', 'Send customer and merchant confirmation after order confirmation.', '["correlation_id","order_id","user_id"]'::jsonb, '["notification.created","order.confirmed"]'::jsonb)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    service = EXCLUDED.service,
    status = EXCLUDED.status,
    description = EXCLUDED.description,
    inputs = EXCLUDED.inputs,
    outputs = EXCLUDED.outputs,
updated_at = now();

\connect ecom_test

SET search_path TO products;
\i /seed/001-seed-ecommerce-test-fragment.sql

SET search_path TO orders;
\i /seed/001-seed-ecommerce-test-orders.sql

SET search_path TO workflow;
\i /seed/001-seed-ecommerce-test-workflow.sql
