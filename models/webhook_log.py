"""
Modèle pour les logs des webhooks CJ
"""
from extensions import db
from datetime import datetime


class WebhookLog(db.Model):
    """Log des webhooks reçus de CJ Dropshipping"""
    
    __tablename__ = 'webhook_log'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    payload = db.Column(db.Text, nullable=True)  # JSON des données reçues
    result = db.Column(db.Text, nullable=True)   # JSON du résultat du traitement
    success = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<WebhookLog {self.event_type} - {self.created_at}>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        import json
        return {
            'id': self.id,
            'event_type': self.event_type,
            'payload': json.loads(self.payload) if self.payload else {},
            'result': json.loads(self.result) if self.result else {},
            'success': self.success,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
