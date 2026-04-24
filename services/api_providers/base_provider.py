"""
Classe de base pour tous les providers d'API
"""
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import time

class BaseApiProvider(ABC):
    """Classe abstraite de base pour tous les providers"""
    
    def __init__(self, api_provider):
        """
        Initialiser le provider
        
        Args:
            api_provider: Instance du modèle ApiProvider
        """
        self.provider = api_provider
        self.api_key = api_provider.api_key
        self.api_secret = api_provider.api_secret
        self.api_endpoint = api_provider.api_endpoint
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configurer la session HTTP"""
        self.session.headers.update({
            'User-Agent': 'MultiProShop/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _check_rate_limit(self):
        """Vérifier les limites de taux"""
        if self.provider.rate_limit:
            if self.provider.requests_today >= self.provider.daily_quota:
                raise Exception(f"Quota journalier atteint ({self.provider.daily_quota})")
        
        # Incrémenter le compteur
        self.provider.increment_requests()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Faire une requête HTTP
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Endpoint de l'API
            **kwargs: Arguments supplémentaires pour requests
        
        Returns:
            Réponse JSON
        """
        self._check_rate_limit()
        
        url = f"{self.api_endpoint}/{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur API: {str(e)}")
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Tester la connexion à l'API"""
        pass
    
    @abstractmethod
    def get_categories(self) -> List[Dict]:
        """Récupérer les catégories du provider"""
        pass
    
    @abstractmethod
    def get_products(self, category_id: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict:
        """
        Récupérer les produits
        
        Args:
            category_id: ID de catégorie (optionnel)
            page: Numéro de page
            limit: Nombre de produits par page
        
        Returns:
            Dict avec 'products' et 'pagination'
        """
        pass
    
    @abstractmethod
    def get_product_details(self, product_id: str) -> Dict:
        """Récupérer les détails d'un produit"""
        pass
    
    @abstractmethod
    def get_product_stock(self, product_id: str, variant_id: Optional[str] = None) -> int:
        """Récupérer le stock d'un produit"""
        pass
    
    @abstractmethod
    def create_order(self, order_data: Dict) -> Dict:
        """
        Créer une commande chez le provider
        
        Args:
            order_data: Données de la commande
        
        Returns:
            Détails de la commande créée
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """Récupérer le statut d'une commande"""
        pass
    
    def translate_product_data(self, raw_data: Dict) -> Dict:
        """
        Traduire les données brutes du provider en format MPS
        
        Args:
            raw_data: Données brutes du provider
        
        Returns:
            Données formatées pour MPS
        """
        # À implémenter dans chaque provider
        return raw_data
    
    def sync_product_stock(self, product_source):
        """
        Synchroniser le stock d'un produit
        
        Args:
            product_source: Instance de ProductSource
        """
        try:
            stock = self.get_product_stock(
                product_source.external_product_id,
                product_source.external_variant_id
            )
            
            # Mettre à jour le stock
            product_source.external_stock = stock
            product_source.product.stock = stock
            product_source.sync_status = 'synced'
            product_source.last_synced_at = time.time()
            
            return True
        except Exception as e:
            product_source.sync_status = 'error'
            product_source.sync_error = str(e)
            return False
