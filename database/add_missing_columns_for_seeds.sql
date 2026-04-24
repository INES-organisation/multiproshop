-- Script idempotent pour ajouter les colonnes et tables nécessaires aux seeds
-- À adapter selon les besoins spécifiques du projet multiproshop

SET @db := DATABASE();

-- Exemple : création d'une table 'users' si elle n'existe pas
SET @table_exists := (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=@db AND TABLE_NAME='users');
SET @sql := IF(@table_exists=0,
  'CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY);',
  'SELECT 1;');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Exemple : ajout d'une colonne 'email' si elle n'existe pas
SET @col := 'email'; SET @type := 'VARCHAR(255) NULL';
SET @sql := IF(NOT EXISTS (SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=@db AND TABLE_NAME='users' AND COLUMN_NAME=@col), CONCAT('ALTER TABLE users ADD COLUMN ', @col, ' ', @type, ';'), 'SELECT 1;');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Ajoute ici d'autres tables/colonnes selon tes seeds
