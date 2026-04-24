"""
Script pour déclencher manuellement la synchronisation des variantes
Utilise Celery pour une exécution asynchrone automatisée
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.variant_sync_tasks import sync_all_variants, sync_missing_variants
import argparse


def main():
    parser = argparse.ArgumentParser(description='Synchroniser les variantes CJ via Celery')
    parser.add_argument(
        '--mode',
        choices=['all', 'missing'],
        default='missing',
        help='Mode de synchronisation: all (tous) ou missing (manquants uniquement)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Nombre de produits par lot (défaut: 50)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=600,
        help='Délai entre les lots en secondes (défaut: 600 = 10 min)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("DÉCLENCHEMENT SYNCHRONISATION VARIANTES CJ")
    print("=" * 80)
    print(f"Mode: {args.mode}")
    print()
    
    if args.mode == 'all':
        print(f"Lancement synchronisation complète...")
        print(f"  - Taille des lots: {args.batch_size} produits")
        print(f"  - Délai entre lots: {args.delay}s")
        print()
        
        # Lancer la tâche Celery
        result = sync_all_variants.delay(
            batch_size=args.batch_size,
            delay_between_batches=args.delay
        )
        
        print(f"✅ Tâche Celery lancée: {result.id}")
        print(f"📊 Suivre l'avancement sur Flower: http://localhost:5555")
        
    else:  # missing
        print("Lancement synchronisation des produits manquants...")
        print()
        
        # Lancer la tâche Celery
        result = sync_missing_variants.delay()
        
        print(f"✅ Tâche Celery lancée: {result.id}")
        print(f"📊 Suivre l'avancement sur Flower: http://localhost:5555")
    
    print()
    print("=" * 80)
    print("La synchronisation s'exécute en arrière-plan via Celery.")
    print("Les tâches continueront même si vous fermez ce script.")
    print("=" * 80)


if __name__ == '__main__':
    main()
