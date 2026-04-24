-- Migration: Ajouter les champs CJ Dropshipping
-- Date: 2026-01-06

-- ============================================================================
-- CATEGORY: Ajouter champs CJ
-- ============================================================================

-- Champs CJ Dropshipping pour catégories
ALTER TABLE category ADD COLUMN cj_category_id VARCHAR(255);
ALTER TABLE category ADD COLUMN name_fr VARCHAR(255);
ALTER TABLE category ADD COLUMN product_count INTEGER DEFAULT 0;
ALTER TABLE category ADD COLUMN visible BOOLEAN DEFAULT 1;
ALTER TABLE category ADD COLUMN last_sync DATETIME;

-- Index pour performances
CREATE INDEX IF NOT EXISTS idx_category_parent ON category(parent_id);
CREATE INDEX IF NOT EXISTS idx_category_level ON category(level);
CREATE UNIQUE INDEX IF NOT EXISTS idx_category_cj_id ON category(cj_category_id);
CREATE INDEX IF NOT EXISTS idx_category_visible ON category(visible);

-- ============================================================================
-- PRODUCT: Ajouter champs CJ
-- ============================================================================

-- Champs CJ Dropshipping pour produits
ALTER TABLE product ADD COLUMN cj_pid VARCHAR(255);
ALTER TABLE product ADD COLUMN suggested_price FLOAT;
ALTER TABLE product ADD COLUMN product_weight VARCHAR(50);
ALTER TABLE product ADD COLUMN material VARCHAR(255);
ALTER TABLE product ADD COLUMN published BOOLEAN DEFAULT 0;
ALTER TABLE product ADD COLUMN synced_at DATETIME;

-- Index pour performances
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_cj_pid ON product(cj_pid);
CREATE INDEX IF NOT EXISTS idx_product_published ON product(published);
CREATE INDEX IF NOT EXISTS idx_product_category ON product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_active ON product(is_active);

-- ============================================================================
-- PRODUCT_VARIANT: Créer table pour variantes
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_variant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    cj_vid VARCHAR(255) UNIQUE NOT NULL,
    variant_key VARCHAR(100),
    color VARCHAR(50),
    size VARCHAR(50),
    price FLOAT,
    suggested_price FLOAT,
    stock INTEGER DEFAULT 0,
    image_url TEXT,
    weight INTEGER,
    sku VARCHAR(100),
    active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(id)
);

-- Index pour variantes
CREATE INDEX IF NOT EXISTS idx_variant_product ON product_variant(product_id);
CREATE INDEX IF NOT EXISTS idx_variant_cj_vid ON product_variant(cj_vid);
CREATE INDEX IF NOT EXISTS idx_variant_active ON product_variant(active);

-- ============================================================================
-- FIN MIGRATION
-- ============================================================================
