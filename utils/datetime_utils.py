"""
Utilitaires pour la gestion des dates et heures
Utilise datetime.now(UTC) au lieu de datetime.utcnow() (deprecated)
"""
from datetime import datetime, timezone, timedelta


def utcnow():
    """
    Retourne la date/heure actuelle en UTC
    Remplace datetime.utcnow() qui est deprecated
    
    Returns:
        datetime: Date/heure actuelle en UTC
    """
    return datetime.now(timezone.utc)


def now_naive():
    """
    Retourne la date/heure actuelle sans timezone (naive)
    Compatible avec SQLite qui ne gère pas les timezones
    
    Returns:
        datetime: Date/heure actuelle naive
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_datetime(dt, format_string='%d/%m/%Y %H:%M'):
    """
    Formater une date/heure
    
    Args:
        dt: datetime à formater
        format_string: Format de sortie
    
    Returns:
        str: Date formatée
    """
    if dt is None:
        return ''
    return dt.strftime(format_string)


def parse_datetime(date_string, format_string='%Y-%m-%d'):
    """
    Parser une chaîne de date
    
    Args:
        date_string: Chaîne à parser
        format_string: Format d'entrée
    
    Returns:
        datetime: Date parsée
    """
    if not date_string:
        return None
    return datetime.strptime(date_string, format_string)


def add_days(dt, days):
    """
    Ajouter des jours à une date
    
    Args:
        dt: datetime de base
        days: Nombre de jours à ajouter
    
    Returns:
        datetime: Nouvelle date
    """
    return dt + timedelta(days=days)


def add_hours(dt, hours):
    """
    Ajouter des heures à une date
    
    Args:
        dt: datetime de base
        hours: Nombre d'heures à ajouter
    
    Returns:
        datetime: Nouvelle date
    """
    return dt + timedelta(hours=hours)


def time_ago(dt):
    """
    Retourne une chaîne "il y a X temps"
    
    Args:
        dt: datetime à comparer
    
    Returns:
        str: Chaîne formatée
    """
    if dt is None:
        return ''
    
    now = now_naive()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "à l'instant"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"il y a {days} jour{'s' if days > 1 else ''}"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"il y a {weeks} semaine{'s' if weeks > 1 else ''}"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"il y a {months} mois"
    else:
        years = int(seconds / 31536000)
        return f"il y a {years} an{'s' if years > 1 else ''}"


def is_past(dt):
    """
    Vérifie si une date est dans le passé
    
    Args:
        dt: datetime à vérifier
    
    Returns:
        bool: True si dans le passé
    """
    if dt is None:
        return False
    return dt < now_naive()


def is_future(dt):
    """
    Vérifie si une date est dans le futur
    
    Args:
        dt: datetime à vérifier
    
    Returns:
        bool: True si dans le futur
    """
    if dt is None:
        return False
    return dt > now_naive()


def days_between(dt1, dt2):
    """
    Calculer le nombre de jours entre deux dates
    
    Args:
        dt1: Première date
        dt2: Deuxième date
    
    Returns:
        int: Nombre de jours
    """
    if dt1 is None or dt2 is None:
        return 0
    diff = abs(dt2 - dt1)
    return diff.days
