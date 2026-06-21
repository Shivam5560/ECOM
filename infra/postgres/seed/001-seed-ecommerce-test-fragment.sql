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
    ('test-aurora-speaker', 'Test Aurora Speaker', 'Audio', 'Seed product for integration tests.', 249, 3, 4.8, '', '#0e5d4e', 'admin-1', 'admin-1', NULL, TRUE),
    ('test-halo-lamp', 'Test Halo Task Lamp', 'Desk', 'Seed lamp for integration tests.', 164, 4, 4.6, '', '#4f6f8f', 'admin-1', 'admin-1', NULL, TRUE)
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
