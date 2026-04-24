#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Synchronisation optimisée RAPIDE pour contourner les rate limits
Stratégie: Synchroniser par petits lots avec délais intelligents
"""

from app import create_app
from celery_app import celery
from models.product import Product
import time

app = create_app()
app.app_context().push()

# Récupérer les 100 derniers produits (nouveaux)
recent_products = Product.query.filter(
    Product.cj_pid.isnot(None),
    Product.published == True,
    Product.stock == 0  # Seulement ceux sans stock
).order_by(Product.id.desc()).limit(100).all()

print(f"🚀 SYNCHRONISATION RAPIDE OPTIMISÉE")
print(f"=" * 60)
print(f"📦 Produits à synchroniser: {len(recent_products)}")
print(f"⚡ Stratégie: 1 produit toutes les 2 secondes")
print(f"⏱️  Durée estimée: {len(recent_products) * 2 / 60:.1f} minutes")
print(f"=" * 60)
print()

# Lancer les tâches avec délai progressif
for i, product in enumerate(recent_products, 1):
    result = celery.send_task(
        'tasks.variant_sync_tasks.sync_product_variants',
        args=[product.id]
    )
    
    print(f"✅ {i:3d}/{len(recent_products)} - ID {product.id:4d}: {product.name[:40]:40s} → {result.id[:8]}...")
    
    # Délai de 2 secondes entre chaque produit
    if i < len(recent_products):
        time.sleep(2)

print()
print(f"=" * 60)
print(f"🎯 {len(recent_products)} tâches lancées avec succès")
print(f"⏳ Attendre ~{len(recent_products) * 2 / 60:.0f} minutes pour la fin")
print(f"📊 Vérifier ensuite les stocks avec:")
print(f"   python -c \"from app import create_app; from models.product import Product; app = create_app(); app.app_context().push(); recent = Product.query.filter(Product.cj_pid.isnot(None), Product.published == True).order_by(Product.id.desc()).limit(10).all(); [print(f'ID {{p.id}}: Stock {{p.stock}}') for p in recent]\"")
print(f"=" * 60)
