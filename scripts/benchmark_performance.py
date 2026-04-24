"""
Script de benchmark complet des performances
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db, cache
from models.product import Product
from models.category import Category
from services.product_service import ProductService
import time

app = create_app()


def benchmark_function(func, name, iterations=100):
    """Benchmark une fonction"""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        func()
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)
    
    avg = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return {
        'name': name,
        'avg': avg,
        'min': min_time,
        'max': max_time,
        'iterations': iterations
    }


def run_benchmarks():
    """Exécuter tous les benchmarks"""
    with app.app_context():
        print("="*70)
        print("⚡ BENCHMARK DE PERFORMANCE MULTIPROSHOP")
        print("="*70)
        print()
        
        results = []
        
        # 1. Requêtes simples
        print("📊 BENCHMARK REQUÊTES SIMPLES")
        print("-"*70)
        
        def query_all_products():
            Product.query.limit(10).all()
        
        result = benchmark_function(query_all_products, "Query 10 produits", 50)
        results.append(result)
        print(f"  {result['name']:40} : {result['avg']:>6.2f} ms (avg)")
        
        def query_active_products():
            Product.query.filter_by(is_active=True).limit(10).all()
        
        result = benchmark_function(query_active_products, "Query produits actifs", 50)
        results.append(result)
        print(f"  {result['name']:40} : {result['avg']:>6.2f} ms (avg)")
        
        print()
        
        # 2. Requêtes avec jointures
        print("🔗 BENCHMARK REQUÊTES AVEC JOINTURES")
        print("-"*70)
        
        def query_with_eager_loading():
            from sqlalchemy.orm import joinedload
            Product.query.options(joinedload(Product.category)).limit(10).all()
        
        result = benchmark_function(query_with_eager_loading, "Query avec eager loading", 50)
        results.append(result)
        print(f"  {result['name']:40} : {result['avg']:>6.2f} ms (avg)")
        
        print()
        
        # 3. Services
        print("⚙️  BENCHMARK SERVICES")
        print("-"*70)
        
        def service_get_products():
            ProductService.get_products_paginated(page=1, per_page=10)
        
        result = benchmark_function(service_get_products, "ProductService.get_products", 50)
        results.append(result)
        print(f"  {result['name']:40} : {result['avg']:>6.2f} ms (avg)")
        
        def service_get_featured():
            ProductService.get_featured_products(limit=8)
        
        result = benchmark_function(service_get_featured, "ProductService.get_featured", 50)
        results.append(result)
        print(f"  {result['name']:40} : {result['avg']:>6.2f} ms (avg)")
        
        print()
        
        # 4. Cache
        print("💾 BENCHMARK CACHE")
        print("-"*70)
        
        # Test cache set
        def cache_set_test():
            cache.set('test_key', 'test_value', timeout=60)
        
        result = benchmark_function(cache_set_test, "Cache SET", 100)
        results.append(result)
        print(f"  {result['name']:40} : {result['avg']:>6.2f} ms (avg)")
        
        # Test cache get
        cache.set('test_key', 'test_value', timeout=60)
        
        def cache_get_test():
            cache.get('test_key')
        
        result = benchmark_function(cache_get_test, "Cache GET", 100)
        results.append(result)
        print(f"  {result['name']:40} : {result['avg']:>6.2f} ms (avg)")
        
        print()
        
        # 5. Résumé
        print("📈 RÉSUMÉ DES PERFORMANCES")
        print("-"*70)
        
        total_avg = sum(r['avg'] for r in results) / len(results)
        
        print(f"  Nombre de tests    : {len(results)}")
        print(f"  Temps moyen global : {total_avg:.2f} ms")
        print()
        
        # Identifier les plus lents
        slowest = sorted(results, key=lambda x: x['avg'], reverse=True)[:3]
        print("  ⚠️  Tests les plus lents :")
        for r in slowest:
            print(f"     - {r['name']:35} : {r['avg']:>6.2f} ms")
        
        print()
        
        # Identifier les plus rapides
        fastest = sorted(results, key=lambda x: x['avg'])[:3]
        print("  ✅ Tests les plus rapides :")
        for r in fastest:
            print(f"     - {r['name']:35} : {r['avg']:>6.2f} ms")
        
        print()
        
        # 6. Évaluation globale
        print("🎯 ÉVALUATION GLOBALE")
        print("-"*70)
        
        if total_avg < 5:
            grade = "🏆 EXCELLENT"
            comment = "Performances exceptionnelles !"
        elif total_avg < 10:
            grade = "✅ TRÈS BON"
            comment = "Très bonnes performances"
        elif total_avg < 20:
            grade = "👍 BON"
            comment = "Bonnes performances"
        elif total_avg < 50:
            grade = "⚠️  MOYEN"
            comment = "Performances acceptables, optimisations possibles"
        else:
            grade = "❌ FAIBLE"
            comment = "Optimisations nécessaires"
        
        print(f"  Note : {grade}")
        print(f"  {comment}")
        print()
        
        print("="*70)
        print("✅ Benchmark terminé")
        print("="*70)


if __name__ == '__main__':
    run_benchmarks()
