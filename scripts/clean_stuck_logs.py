import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.api_provider import ApiSyncLog
from datetime import datetime

with app.app_context():
    print("\n" + "="*80)
    print("NETTOYAGE DES LOGS BLOQUÉS")
    print("="*80 + "\n")
    
    # Trouver tous les logs en statut "running"
    stuck_logs = ApiSyncLog.query.filter_by(status='running').all()
    
    print(f"Logs bloqués trouvés: {len(stuck_logs)}\n")
    
    for log in stuck_logs:
        print(f"Log ID {log.id}:")
        print(f"  Démarré: {log.started_at}")
        print(f"  Statut: {log.status} → cancelled")
        
        # Marquer comme annulé
        log.status = 'cancelled'
        log.completed_at = datetime.utcnow()
        print()
    
    db.session.commit()
    
    print("="*80)
    print(f"✓ {len(stuck_logs)} logs nettoyés")
    print("="*80 + "\n")
