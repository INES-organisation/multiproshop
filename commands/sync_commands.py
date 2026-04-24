"""
Commandes Flask pour la synchronisation CJ
"""
import click
from flask.cli import with_appcontext
from extensions import db
from services.background_sync_service import BackgroundSyncService
from services.cj_api_service import CjApiService
import logging

logger = logging.getLogger(__name__)


@click.group()
def sync():
    """Commandes de synchronisation CJ"""
    pass


@sync.command()
@click.option('--batch-size', default=10, help='Nombre de produits par batch')
@with_appcontext
def batch(batch_size):
    """Synchroniser un batch de produits"""
    click.echo(f"🔄 Synchronisation d'un batch de {batch_size} produits...")
    
    cj_api = CjApiService()
    sync_service = BackgroundSyncService(db, cj_api)
    
    result = sync_service.sync_batch(batch_size)
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
        click.echo(f"   • Synchronisés: {result['synced']}")
        click.echo(f"   • Échecs: {result['failed']}")
        click.echo(f"   • Durée: {result['duration']}")
    else:
        click.echo(f"❌ {result['message']}", err=True)


@sync.command()
@click.argument('product_id', type=int)
@with_appcontext
def product(product_id):
    """Synchroniser un produit spécifique"""
    click.echo(f"🔄 Synchronisation du produit {product_id}...")
    
    cj_api = CjApiService()
    sync_service = BackgroundSyncService(db, cj_api)
    
    result = sync_service.sync_single_product(product_id)
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
        if result.get('changes'):
            click.echo("   Changements détectés:")
            for key, value in result['changes'].items():
                if isinstance(value, dict) and 'old' in value:
                    click.echo(f"   • {key}: {value['old']} → {value['new']}")
                else:
                    click.echo(f"   • {key}: {value}")
    else:
        click.echo(f"❌ {result['message']}", err=True)


@sync.command()
@with_appcontext
def stats():
    """Afficher les statistiques de synchronisation"""
    cj_api = CjApiService()
    sync_service = BackgroundSyncService(db, cj_api)
    
    stats = sync_service.get_sync_stats()
    
    click.echo("\n📊 STATISTIQUES DE SYNCHRONISATION")
    click.echo("=" * 50)
    click.echo(f"Total produits CJ:        {stats.get('total_cj_products', 0)}")
    click.echo(f"Produits actifs:          {stats.get('active_cj_products', 0)}")
    click.echo(f"Jamais synchronisés:      {stats.get('never_synced', 0)}")
    click.echo(f"Synchronisés 24h:         {stats.get('synced_last_24h', 0)}")
    click.echo(f"Stock bas (<10):          {stats.get('low_stock', 0)}")
    click.echo(f"Rupture de stock:         {stats.get('out_of_stock', 0)}")
    click.echo("=" * 50)
    
    if stats.get('can_sync'):
        click.echo("✅ Peut synchroniser maintenant")
    else:
        wait_time = stats.get('wait_time', 0)
        click.echo(f"⏳ Attendre {wait_time}s avant la prochaine sync")


@sync.command()
@with_appcontext
def worker():
    """Lancer le worker de synchronisation en arrière-plan"""
    click.echo("🚀 Démarrage du worker de synchronisation...")
    click.echo("   Appuyez sur Ctrl+C pour arrêter")
    click.echo("")
    
    from workers.sync_worker import SyncWorker
    
    worker = SyncWorker()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        click.echo("\n⚠️ Arrêt du worker...")
        worker.stop()


def init_app(app):
    """Enregistrer les commandes dans l'application Flask"""
    app.cli.add_command(sync)
