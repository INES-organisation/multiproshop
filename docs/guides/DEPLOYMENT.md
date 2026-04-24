# 🚀 GUIDE DE DÉPLOIEMENT PRODUCTION

**Version** : 1.0  
**Date** : 6 janvier 2026  
**Projet** : MultiProShop - Intégration CJ

---

## 📋 PRÉ-REQUIS

### Serveur
- Ubuntu 20.04+ ou Debian 11+
- 2 CPU minimum
- 4 GB RAM minimum
- 50 GB stockage
- Accès SSH root ou sudo

### Logiciels
- Python 3.9+
- PostgreSQL 14+ (recommandé) ou MySQL 8+
- Redis 6+
- Nginx 1.18+
- Certbot (Let's Encrypt)

---

## 🔧 INSTALLATION

### 1. Préparation du serveur

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y python3-pip python3-venv nginx redis-server postgresql postgresql-contrib git

# Créer utilisateur dédié
sudo useradd -m -s /bin/bash multiproshop
sudo su - multiproshop
```

### 2. Cloner le projet

```bash
cd /home/multiproshop
git clone https://github.com/votre-repo/multiproshop.git
cd multiproshop
```

### 3. Environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_phase_7.txt
pip install gunicorn
```

### 4. Configuration PostgreSQL

```bash
# Créer base de données
sudo -u postgres psql

CREATE DATABASE multiproshop;
CREATE USER multiproshop WITH PASSWORD 'mot_de_passe_securise';
GRANT ALL PRIVILEGES ON DATABASE multiproshop TO multiproshop;
\q
```

### 5. Configuration Redis

```bash
# Éditer la configuration
sudo nano /etc/redis/redis.conf

# Modifier:
bind 127.0.0.1
maxmemory 256mb
maxmemory-policy allkeys-lru

# Redémarrer
sudo systemctl restart redis
sudo systemctl enable redis
```

### 6. Variables d'environnement

```bash
# Créer fichier .env
nano /home/multiproshop/multiproshop/.env
```

```env
# Production
FLASK_ENV=production
SECRET_KEY=generer_une_cle_super_longue_et_aleatoire_ici

# Base de données
DATABASE_URL=postgresql://multiproshop:mot_de_passe@localhost/multiproshop

# Redis
REDIS_URL=redis://localhost:6379/0

# CJ Dropshipping
CJ_EMAIL=votre_email@gmail.com
CJ_PASSWORD=votre_mot_de_passe
CJ_DEV_KEY=votre_dev_key

# Stripe
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=mot_de_passe_application

# Sentry (monitoring)
SENTRY_DSN=https://...@sentry.io/...
```

### 7. Migration base de données

```bash
source venv/bin/activate
python database/migrations/run_migration.py
```

---

## 🌐 CONFIGURATION NGINX

### 1. Créer configuration

```bash
sudo nano /etc/nginx/sites-available/multiproshop
```

```nginx
server {
    listen 80;
    server_name multiproshop.com www.multiproshop.com;

    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name multiproshop.com www.multiproshop.com;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/multiproshop.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/multiproshop.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logs
    access_log /var/log/nginx/multiproshop_access.log;
    error_log /var/log/nginx/multiproshop_error.log;

    # Fichiers statiques
    location /static {
        alias /home/multiproshop/multiproshop/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy vers Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 2. Activer la configuration

```bash
sudo ln -s /etc/nginx/sites-available/multiproshop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 CONFIGURATION SSL (Let's Encrypt)

```bash
# Installer Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtenir certificat
sudo certbot --nginx -d multiproshop.com -d www.multiproshop.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
```

---

## 🔄 SERVICE SYSTEMD

### 1. Créer service Gunicorn

```bash
sudo nano /etc/systemd/system/multiproshop.service
```

```ini
[Unit]
Description=MultiProShop Gunicorn
After=network.target

[Service]
User=multiproshop
Group=www-data
WorkingDirectory=/home/multiproshop/multiproshop
Environment="PATH=/home/multiproshop/multiproshop/venv/bin"
ExecStart=/home/multiproshop/multiproshop/venv/bin/gunicorn \
    --workers 4 \
    --worker-class gevent \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/multiproshop/access.log \
    --error-logfile /var/log/multiproshop/error.log \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Créer dossier logs

```bash
sudo mkdir -p /var/log/multiproshop
sudo chown multiproshop:www-data /var/log/multiproshop
```

### 3. Activer et démarrer

```bash
sudo systemctl daemon-reload
sudo systemctl enable multiproshop
sudo systemctl start multiproshop
sudo systemctl status multiproshop
```

---

## 📊 MONITORING

### 1. Sentry (erreurs)

```python
# Dans app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=Config.SENTRY_DSN,
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

### 2. Logs structurés

```bash
# Rotation des logs
sudo nano /etc/logrotate.d/multiproshop
```

```
/var/log/multiproshop/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 multiproshop www-data
    sharedscripts
    postrotate
        systemctl reload multiproshop
    endscript
}
```

---

## 💾 SAUVEGARDES

### 1. Script de backup

```bash
nano /home/multiproshop/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/multiproshop/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer dossier
mkdir -p $BACKUP_DIR

# Backup BDD
pg_dump -U multiproshop multiproshop | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup fichiers
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /home/multiproshop/multiproshop/static/images

# Garder 7 jours
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup terminé: $DATE"
```

### 2. Cron quotidien

```bash
chmod +x /home/multiproshop/backup.sh
crontab -e

# Ajouter:
0 2 * * * /home/multiproshop/backup.sh >> /var/log/multiproshop/backup.log 2>&1
```

---

## 🔐 SÉCURITÉ

### 1. Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Permissions

```bash
# Fichiers
sudo chown -R multiproshop:www-data /home/multiproshop/multiproshop
sudo chmod -R 755 /home/multiproshop/multiproshop
sudo chmod 600 /home/multiproshop/multiproshop/.env
```

---

## ✅ CHECKLIST DÉPLOIEMENT

- [ ] Serveur configuré
- [ ] PostgreSQL installé et configuré
- [ ] Redis installé et configuré
- [ ] Nginx installé et configuré
- [ ] SSL activé (Let's Encrypt)
- [ ] Variables `.env` configurées
- [ ] Base de données migrée
- [ ] Service systemd créé et actif
- [ ] Logs configurés
- [ ] Sauvegardes automatiques
- [ ] Monitoring Sentry activé
- [ ] Firewall configuré
- [ ] Tests de charge effectués
- [ ] DNS configuré
- [ ] Email de notification configuré

---

## 🧪 TESTS POST-DÉPLOIEMENT

```bash
# Test connexion
curl -I https://multiproshop.com

# Test API
curl https://multiproshop.com/api/shipping/methods?country=FR

# Test admin
curl https://multiproshop.com/admin/cj/categories

# Logs en temps réel
sudo journalctl -u multiproshop -f
```

---

## 🔄 MISE À JOUR

```bash
# Se connecter au serveur
ssh multiproshop@votre-serveur

# Aller dans le projet
cd /home/multiproshop/multiproshop

# Sauvegarder
./backup.sh

# Mettre à jour
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Migrations si nécessaire
python database/migrations/run_migration.py

# Redémarrer
sudo systemctl restart multiproshop
```

---

## 📞 SUPPORT

**Logs** :
- Application : `/var/log/multiproshop/`
- Nginx : `/var/log/nginx/`
- Système : `journalctl -u multiproshop`

**Commandes utiles** :
```bash
# Status
sudo systemctl status multiproshop

# Redémarrer
sudo systemctl restart multiproshop

# Logs
sudo journalctl -u multiproshop -n 100

# Test Nginx
sudo nginx -t
```

---

**Document créé le** : 6 janvier 2026  
**Version** : 1.0  
**Projet** : MultiProShop - Guide déploiement
