# Scripts archivés - Phase 3 Nettoyage

**Date d'archivage:** 28 Janvier 2026  
**Raison:** Scripts de test et debug obsolètes après optimisation CJ

## Scripts archivés

Ces scripts ont été utilisés pendant le développement et le debug de l'intégration CJ Dropshipping.
Ils sont maintenant obsolètes car remplacés par des solutions plus robustes.

### Scripts de test CJ (32 fichiers)
- test_cj_*.py - Tests API CJ
- test_sync_*.py - Tests synchronisation
- test_variants_*.py - Tests variantes
- test_admin_login.py - Test login admin
- test_env_loading.py - Test chargement .env
- test_formatted_product.py - Test formatage produits
- test_login_flow.py - Test flux login
- test_phase_3.py - Test phase 3
- test_pricing_service.py - Test service pricing
- test_products_*.py - Tests produits
- test_redis.py - Test Redis
- test_webhooks_cj.py - Test webhooks

### Scripts de debug (6 fichiers)
- debug_admin.py - Debug admin
- debug_categories_sync.py - Debug sync catégories
- debug_category_products.py - Debug produits par catégorie
- debug_cj_sync.py - Debug sync CJ
- debug_simple.py - Debug simple
- debug_sync.py - Debug synchronisation

### Scripts utilitaires obsolètes (4 fichiers)
- quick_sync_test.py - Test sync rapide
- simple_test_variants.py - Test simple variantes
- exemples_utilisation.py - Exemples utilisation
- verify_cj_config.py - Vérification config CJ

## Scripts conservés (production)

Les scripts suivants restent actifs car utilisés en production:

### CRON Jobs
- cron_sync_products.py
- cron_sync_stock.py
- cron_sync_orders.py

### Configuration
- setup_cj_webhooks.py
- configure_cj_provider.py
- create_admin.py

### Synchronisation
- sync_all_stocks_from_cj.py
- sync_product_variants.py
- sync_category_counts_all_levels.py

### Maintenance
- recalculate_all_prices.py
- update_category_counts.py
- clean_stuck_logs.py

## Restauration

Si besoin de restaurer un script:
```bash
cp archive_phase3/nom_du_script.py .
```
