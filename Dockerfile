# Image unique pour le site (gunicorn) et le worker Celery — voir deploy/docker-compose.yml
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Utilisateur sans droits ; instance/ et static/gen/ doivent rester inscriptibles
RUN useradd --create-home --uid 1000 app \
    && mkdir -p instance logs static/gen static/uploads \
    && chown -R app:app /app
USER app

EXPOSE 8000

# 2 workers × 4 threads, application chargée une fois (--preload) : ~160 Mo sur un VPS partagé
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "60", "--preload", "--access-logfile", "-"]
