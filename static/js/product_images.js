/**
 * Gestionnaire de galerie d'images produit
 * Gère l'affichage et la navigation des images CJ
 */

class ProductImageGallery {
    constructor(images) {
        this.images = images || [];
        this.currentIndex = 0;
        this.init();
    }
    
    init() {
        if (this.images.length > 0) {
            this.renderGallery();
            this.attachEvents();
        }
    }
    
    renderGallery() {
        // Afficher l'image principale
        this.updateMainImage(0);
        
        // Afficher les miniatures
        this.renderThumbnails();
    }
    
    renderThumbnails() {
        const container = document.getElementById('product-thumbnails');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.images.forEach((image, index) => {
            const thumbnail = document.createElement('div');
            thumbnail.className = `thumbnail ${index === 0 ? 'active' : ''}`;
            thumbnail.dataset.index = index;
            thumbnail.innerHTML = `<img src="${image}" alt="Image ${index + 1}" loading="lazy">`;
            
            thumbnail.addEventListener('click', () => {
                this.selectImage(index);
            });
            
            container.appendChild(thumbnail);
        });
    }
    
    selectImage(index) {
        if (index < 0 || index >= this.images.length) return;
        
        this.currentIndex = index;
        this.updateMainImage(index);
        this.updateThumbnails(index);
    }
    
    updateMainImage(index) {
        const mainImage = document.getElementById('mainImage');
        if (mainImage && this.images[index]) {
            mainImage.src = this.images[index];
            
            // Animation de transition
            mainImage.style.opacity = '0';
            setTimeout(() => {
                mainImage.style.opacity = '1';
            }, 100);
        }
    }
    
    updateThumbnails(index) {
        document.querySelectorAll('.thumbnail').forEach((thumb, i) => {
            thumb.classList.toggle('active', i === index);
        });
    }
    
    nextImage() {
        const nextIndex = (this.currentIndex + 1) % this.images.length;
        this.selectImage(nextIndex);
    }
    
    previousImage() {
        const prevIndex = (this.currentIndex - 1 + this.images.length) % this.images.length;
        this.selectImage(prevIndex);
    }
    
    attachEvents() {
        // Navigation clavier
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.previousImage();
            } else if (e.key === 'ArrowRight') {
                this.nextImage();
            }
        });
        
        // Zoom sur l'image principale
        const mainImage = document.getElementById('mainImage');
        if (mainImage) {
            mainImage.addEventListener('click', () => {
                this.openLightbox(this.currentIndex);
            });
        }
    }
    
    openLightbox(index) {
        // Créer la lightbox
        const lightbox = document.createElement('div');
        lightbox.className = 'image-lightbox';
        lightbox.innerHTML = `
            <div class="lightbox-overlay"></div>
            <div class="lightbox-content">
                <button class="lightbox-close">&times;</button>
                <button class="lightbox-prev">&lsaquo;</button>
                <img src="${this.images[index]}" alt="Image ${index + 1}">
                <button class="lightbox-next">&rsaquo;</button>
                <div class="lightbox-counter">${index + 1} / ${this.images.length}</div>
            </div>
        `;
        
        document.body.appendChild(lightbox);
        
        // Événements lightbox
        let currentLightboxIndex = index;
        
        const updateLightboxImage = (newIndex) => {
            currentLightboxIndex = newIndex;
            const img = lightbox.querySelector('img');
            const counter = lightbox.querySelector('.lightbox-counter');
            img.src = this.images[newIndex];
            counter.textContent = `${newIndex + 1} / ${this.images.length}`;
        };
        
        lightbox.querySelector('.lightbox-close').addEventListener('click', () => {
            lightbox.remove();
        });
        
        lightbox.querySelector('.lightbox-overlay').addEventListener('click', () => {
            lightbox.remove();
        });
        
        lightbox.querySelector('.lightbox-prev').addEventListener('click', () => {
            const prevIndex = (currentLightboxIndex - 1 + this.images.length) % this.images.length;
            updateLightboxImage(prevIndex);
        });
        
        lightbox.querySelector('.lightbox-next').addEventListener('click', () => {
            const nextIndex = (currentLightboxIndex + 1) % this.images.length;
            updateLightboxImage(nextIndex);
        });
        
        // Navigation clavier dans lightbox
        const keyHandler = (e) => {
            if (e.key === 'Escape') {
                lightbox.remove();
                document.removeEventListener('keydown', keyHandler);
            } else if (e.key === 'ArrowLeft') {
                const prevIndex = (currentLightboxIndex - 1 + this.images.length) % this.images.length;
                updateLightboxImage(prevIndex);
            } else if (e.key === 'ArrowRight') {
                const nextIndex = (currentLightboxIndex + 1) % this.images.length;
                updateLightboxImage(nextIndex);
            }
        };
        
        document.addEventListener('keydown', keyHandler);
    }
}

// Fonction pour charger les images d'un produit
async function loadProductImages(productId) {
    try {
        const response = await fetch(`/api/products/${productId}`);
        const data = await response.json();
        
        if (data.success && data.product.images && data.product.images.length > 0) {
            return new ProductImageGallery(data.product.images);
        }
        
        return null;
    } catch (error) {
        console.error('Erreur chargement images:', error);
        return null;
    }
}
