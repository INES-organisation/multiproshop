"""
Service de gestion des images produits
Téléchargement, optimisation, compression et génération miniatures
"""
import os
import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ImageService:
    """Service pour gérer les images produits"""
    
    def __init__(self, base_path: str = 'static/images/products'):
        """
        Initialiser le service d'images
        
        Args:
            base_path: Chemin de base pour stocker les images
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Tailles des miniatures
        self.thumbnail_sizes = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (600, 600)
        }
    
    def download_image(self, url: str, product_id: int) -> Optional[str]:
        """
        Télécharger une image depuis une URL
        
        Args:
            url: URL de l'image
            product_id: ID du produit
            
        Returns:
            str: Chemin relatif de l'image téléchargée ou None
        """
        try:
            # Générer un nom de fichier unique
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"product_{product_id}_{url_hash}.jpg"
            filepath = self.base_path / filename
            
            # Vérifier si l'image existe déjà
            if filepath.exists():
                logger.info(f"Image déjà téléchargée: {filename}")
                return str(filepath.relative_to('static'))
            
            # Télécharger l'image
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Sauvegarder l'image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Image téléchargée: {filename}")
            return str(filepath.relative_to('static'))
            
        except Exception as e:
            logger.error(f"Erreur téléchargement image {url}: {e}")
            return None
    
    def optimize_image(self, image_path: str, quality: int = 85) -> bool:
        """
        Optimiser une image (compression)
        
        Args:
            image_path: Chemin de l'image
            quality: Qualité de compression (1-100)
            
        Returns:
            bool: True si succès
        """
        try:
            filepath = Path('static') / image_path if not image_path.startswith('static') else Path(image_path)
            
            if not filepath.exists():
                logger.warning(f"Image non trouvée: {filepath}")
                return False
            
            # Ouvrir et optimiser l'image
            with Image.open(filepath) as img:
                # Convertir en RGB si nécessaire
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Sauvegarder avec compression
                img.save(filepath, 'JPEG', quality=quality, optimize=True)
            
            logger.info(f"Image optimisée: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur optimisation image {image_path}: {e}")
            return False
    
    def convert_to_webp(self, image_path: str, quality: int = 85) -> Optional[str]:
        """
        Convertir une image en WebP
        
        Args:
            image_path: Chemin de l'image source
            quality: Qualité WebP (1-100)
            
        Returns:
            str: Chemin de l'image WebP ou None
        """
        try:
            filepath = Path('static') / image_path if not image_path.startswith('static') else Path(image_path)
            
            if not filepath.exists():
                logger.warning(f"Image non trouvée: {filepath}")
                return None
            
            # Générer le chemin WebP
            webp_path = filepath.with_suffix('.webp')
            
            # Convertir en WebP
            with Image.open(filepath) as img:
                # Convertir en RGB si nécessaire
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Sauvegarder en WebP
                img.save(webp_path, 'WEBP', quality=quality, method=6)
            
            logger.info(f"Image convertie en WebP: {webp_path}")
            return str(webp_path.relative_to('static'))
            
        except Exception as e:
            logger.error(f"Erreur conversion WebP {image_path}: {e}")
            return None
    
    def generate_thumbnails(self, image_path: str) -> Dict[str, str]:
        """
        Générer des miniatures de différentes tailles
        
        Args:
            image_path: Chemin de l'image source
            
        Returns:
            dict: Chemins des miniatures générées {size: path}
        """
        thumbnails = {}
        
        try:
            filepath = Path('static') / image_path if not image_path.startswith('static') else Path(image_path)
            
            if not filepath.exists():
                logger.warning(f"Image non trouvée: {filepath}")
                return thumbnails
            
            # Créer le dossier thumbnails
            thumb_dir = filepath.parent / 'thumbnails'
            thumb_dir.mkdir(exist_ok=True)
            
            # Générer chaque taille
            with Image.open(filepath) as img:
                for size_name, size in self.thumbnail_sizes.items():
                    # Créer la miniature
                    img_copy = img.copy()
                    img_copy.thumbnail(size, Image.Resampling.LANCZOS)
                    
                    # Générer le nom de fichier
                    thumb_filename = f"{filepath.stem}_{size_name}{filepath.suffix}"
                    thumb_path = thumb_dir / thumb_filename
                    
                    # Sauvegarder
                    if img_copy.mode in ('RGBA', 'P'):
                        img_copy = img_copy.convert('RGB')
                    
                    img_copy.save(thumb_path, 'JPEG', quality=85, optimize=True)
                    
                    # Ajouter au dictionnaire
                    thumbnails[size_name] = str(thumb_path.relative_to('static'))
                    
                    logger.info(f"Miniature {size_name} générée: {thumb_path}")
            
            return thumbnails
            
        except Exception as e:
            logger.error(f"Erreur génération miniatures {image_path}: {e}")
            return thumbnails
    
    def process_product_image(self, url: str, product_id: int, 
                            optimize: bool = True, 
                            webp: bool = True,
                            thumbnails: bool = True) -> Dict[str, any]:
        """
        Traiter complètement une image produit
        
        Args:
            url: URL de l'image
            product_id: ID du produit
            optimize: Optimiser l'image
            webp: Convertir en WebP
            thumbnails: Générer miniatures
            
        Returns:
            dict: Informations sur l'image traitée
        """
        result = {
            'success': False,
            'original': None,
            'webp': None,
            'thumbnails': {},
            'error': None
        }
        
        try:
            # Télécharger l'image
            image_path = self.download_image(url, product_id)
            
            if not image_path:
                result['error'] = 'Échec téléchargement'
                return result
            
            result['original'] = image_path
            
            # Optimiser
            if optimize:
                self.optimize_image(image_path, quality=85)
            
            # Convertir en WebP
            if webp:
                webp_path = self.convert_to_webp(image_path, quality=85)
                if webp_path:
                    result['webp'] = webp_path
            
            # Générer miniatures
            if thumbnails:
                thumbs = self.generate_thumbnails(image_path)
                result['thumbnails'] = thumbs
            
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"Erreur traitement image {url}: {e}")
            result['error'] = str(e)
            return result
    
    def get_image_info(self, image_path: str) -> Optional[Dict]:
        """
        Obtenir les informations d'une image
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            dict: Informations sur l'image
        """
        try:
            filepath = Path('static') / image_path if not image_path.startswith('static') else Path(image_path)
            
            if not filepath.exists():
                return None
            
            with Image.open(filepath) as img:
                return {
                    'path': image_path,
                    'size': filepath.stat().st_size,
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
                
        except Exception as e:
            logger.error(f"Erreur lecture info image {image_path}: {e}")
            return None
    
    def delete_image(self, image_path: str, delete_thumbnails: bool = True) -> bool:
        """
        Supprimer une image et ses miniatures
        
        Args:
            image_path: Chemin de l'image
            delete_thumbnails: Supprimer aussi les miniatures
            
        Returns:
            bool: True si succès
        """
        try:
            filepath = Path('static') / image_path if not image_path.startswith('static') else Path(image_path)
            
            if not filepath.exists():
                logger.warning(f"Image non trouvée: {filepath}")
                return False
            
            # Supprimer les miniatures
            if delete_thumbnails:
                thumb_dir = filepath.parent / 'thumbnails'
                if thumb_dir.exists():
                    for size_name in self.thumbnail_sizes.keys():
                        thumb_filename = f"{filepath.stem}_{size_name}{filepath.suffix}"
                        thumb_path = thumb_dir / thumb_filename
                        if thumb_path.exists():
                            thumb_path.unlink()
                            logger.info(f"Miniature supprimée: {thumb_path}")
            
            # Supprimer l'image principale
            filepath.unlink()
            logger.info(f"Image supprimée: {filepath}")
            
            # Supprimer WebP si existe
            webp_path = filepath.with_suffix('.webp')
            if webp_path.exists():
                webp_path.unlink()
                logger.info(f"WebP supprimé: {webp_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression image {image_path}: {e}")
            return False


def get_image_service() -> ImageService:
    """Obtenir une instance du service d'images"""
    return ImageService()
