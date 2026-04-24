#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour synchroniser les 100 derniers produits publiés
"""

from app import create_app
from celery_app import celery
from models.product import Product

app = create_app()
app.app_context().push()

# Récupérer les 100 derniers produits
recent_products = Product.query.filter(
    Product.cj_pid.isnot(None),
    Product.published == True
).order_by(Product.id.desc()).limit(100).all()

print(f"🔄 Synchronisation de {len(recent_products)} produits récents")
print(f"   IDs: {recent_products[0].id} à {recent_products[-1].id}")
print()

# Lancer la synchronisation pour chaque produit
for i, product in enumerate(recent_products[:10], 1):
    result = celery.send_task(
        'tasks.variant_sync_tasks.sync_product_variants',
        args=[product.id]
    )
    print(f"✅ {i}/10 - Produit {product.id}: {product.name[:40]}... → {result.id}")

print()
print("🎯 10 premières tâches lancées")
print("⏳ Attendre 2-3 minutes puis vérifier les stocks")
