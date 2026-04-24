"""
Service de traduction automatique pour les produits
Supporte Google Translate et DeepL
"""
from typing import Dict, List, Optional
import requests
import hashlib
from extensions import cache

class TranslationService:
    """Service de traduction pour les données produits"""
    
    def __init__(self, provider: str = 'google', api_key: Optional[str] = None):
        """
        Initialiser le service de traduction
        
        Args:
            provider: 'google' ou 'deepl'
            api_key: Clé API (optionnel pour Google Translate gratuit)
        """
        self.provider = provider
        self.api_key = api_key
        
        if provider == 'google' and not api_key:
            # Utiliser googletrans (gratuit, sans clé API)
            try:
                from googletrans import Translator
                self.translator = Translator()
                self.use_library = True
            except (ImportError, Exception) as e:
                print(f"⚠️  googletrans non disponible: {e}")
                print("   La traduction sera désactivée (texte original retourné)")
                self.use_library = False
        elif provider == 'deepl':
            self.deepl_endpoint = 'https://api-free.deepl.com/v2/translate'
            self.use_library = False
        else:
            self.use_library = False
    
    def translate_text(self, text: str, source_lang: str = 'en', target_lang: str = 'fr') -> str:
        """
        Traduire un texte avec cache Redis
        
        Args:
            text: Texte à traduire
            source_lang: Langue source (en, es, de, etc.)
            target_lang: Langue cible (fr, en, es, etc.)
        
        Returns:
            Texte traduit
        """
        if not text or text.strip() == '':
            return text
        
        # Générer clé de cache
        cache_key = self._get_cache_key(text, source_lang, target_lang)
        
        # Vérifier le cache
        try:
            cached = cache.get(cache_key)
            if cached:
                return cached
        except:
            pass
        
        # Traduire si pas en cache
        try:
            if self.provider == 'google' and self.use_library:
                translated = self._translate_google_library(text, source_lang, target_lang)
            elif self.provider == 'deepl':
                translated = self._translate_deepl(text, source_lang, target_lang)
            else:
                # Fallback: retourner le texte original
                translated = text
            
            # Mettre en cache (30 jours)
            try:
                cache.set(cache_key, translated, timeout=2592000)
            except:
                pass
            
            return translated
        except Exception as e:
            print(f"Erreur traduction: {e}")
            return text
    
    def _translate_google_library(self, text: str, source_lang: str, target_lang: str) -> str:
        """Traduire avec googletrans (gratuit)"""
        result = self.translator.translate(text, src=source_lang, dest=target_lang)
        return result.text
    
    def _translate_deepl(self, text: str, source_lang: str, target_lang: str) -> str:
        """Traduire avec DeepL API"""
        if not self.api_key:
            return text
        
        headers = {
            'Authorization': f'DeepL-Auth-Key {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'text': [text],
            'source_lang': source_lang.upper(),
            'target_lang': target_lang.upper()
        }
        
        response = requests.post(self.deepl_endpoint, headers=headers, json=data)
        
        if response.status_code == 200:
            translations = response.json().get('translations', [])
            if translations:
                return translations[0].get('text', text)
        
        return text
    
    def translate_product(self, product_data: Dict, source_lang: str = 'en', target_lang: str = 'fr') -> Dict:
        """
        Traduire toutes les données d'un produit
        
        Args:
            product_data: Données du produit
            source_lang: Langue source
            target_lang: Langue cible
        
        Returns:
            Données traduites
        """
        translated = product_data.copy()
        
        # Traduire le nom
        if 'name' in translated:
            translated['name'] = self.translate_text(translated['name'], source_lang, target_lang)
        
        # Traduire la description
        if 'description' in translated:
            translated['description'] = self.translate_text(translated['description'], source_lang, target_lang)
        
        # Traduire les features (si liste)
        if 'features' in translated and isinstance(translated['features'], list):
            translated['features'] = [
                self.translate_text(feature, source_lang, target_lang)
                for feature in translated['features']
            ]
        
        # Traduire le nom de catégorie
        if 'category_name' in translated:
            translated['category_name'] = self.translate_text(translated['category_name'], source_lang, target_lang)
        
        return translated
    
    def translate_batch(self, texts: List[str], source_lang: str = 'en', target_lang: str = 'fr') -> List[str]:
        """
        Traduire plusieurs textes en batch
        
        Args:
            texts: Liste de textes à traduire
            source_lang: Langue source
            target_lang: Langue cible
        
        Returns:
            Liste de textes traduits
        """
        if self.provider == 'deepl' and self.api_key:
            return self._translate_deepl_batch(texts, source_lang, target_lang)
        else:
            # Traduire un par un
            return [self.translate_text(text, source_lang, target_lang) for text in texts]
    
    def _translate_deepl_batch(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """Traduire en batch avec DeepL"""
        headers = {
            'Authorization': f'DeepL-Auth-Key {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'text': texts,
            'source_lang': source_lang.upper(),
            'target_lang': target_lang.upper()
        }
        
        response = requests.post(self.deepl_endpoint, headers=headers, json=data)
        
        if response.status_code == 200:
            translations = response.json().get('translations', [])
            return [t.get('text', texts[i]) for i, t in enumerate(translations)]
        
        return texts
    
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Générer une clé de cache unique pour une traduction
        
        Args:
            text: Texte à traduire
            source_lang: Langue source
            target_lang: Langue cible
        
        Returns:
            Clé de cache
        """
        # Hash du texte pour éviter les clés trop longues
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"translation:{self.provider}:{source_lang}:{target_lang}:{text_hash}"
    
    def detect_language(self, text: str) -> str:
        """
        Détecter la langue d'un texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            Code langue (en, fr, es, etc.)
        """
        if self.provider == 'google' and self.use_library:
            try:
                result = self.translator.detect(text)
                return result.lang
            except:
                return 'en'
        
        # Fallback: supposer anglais
        return 'en'


# Instance globale (singleton)
_translation_service = None

def get_translation_service(provider: str = 'google', api_key: Optional[str] = None) -> TranslationService:
    """Obtenir l'instance du service de traduction"""
    global _translation_service
    
    if _translation_service is None:
        _translation_service = TranslationService(provider, api_key)
    
    return _translation_service
