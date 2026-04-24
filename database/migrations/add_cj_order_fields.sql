-- Migration pour ajouter les champs CJ aux tables Order et OrderItem
-- Date: 2026-01-23

-- Ajouter les champs CJ à la table Order
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_order_id VARCHAR(100);
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_tracking_number VARCHAR(100);
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_status VARCHAR(50);
ALTER TABLE "order" ADD COLUMN IF NOT EXISTS cj_logistics_name VARCHAR(100);

-- Ajouter le champ variant_id à la table OrderItem
ALTER TABLE order_item ADD COLUMN IF NOT EXISTS variant_id INTEGER REFERENCES product_variant(id);

-- Créer des index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_order_cj_order_id ON "order"(cj_order_id);
CREATE INDEX IF NOT EXISTS idx_order_cj_status ON "order"(cj_status);
CREATE INDEX IF NOT EXISTS idx_order_item_variant_id ON order_item(variant_id);

-- Commentaires
COMMENT ON COLUMN "order".cj_order_id IS 'ID de la commande sur CJ Dropshipping';
COMMENT ON COLUMN "order".cj_tracking_number IS 'Numéro de suivi CJ';
COMMENT ON COLUMN "order".cj_status IS 'Statut de la commande sur CJ';
COMMENT ON COLUMN "order".cj_logistics_name IS 'Nom du transporteur CJ';
COMMENT ON COLUMN order_item.variant_id IS 'ID de la variante de produit sélectionnée';
