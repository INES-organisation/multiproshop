/**
 * Gestionnaire de page produit complète avec support CJ
 * Gère galerie, variantes, stock, livraison
 */

class ProductDetailManager {
    constructor(productId) {
        this.productId = productId;
        this.selectedVariant = null;
        this.variants = [];
        this.images = [];
        this.currentImageIndex = 0;
        this.shippingMethods = [];
        this.selectedCountry = 'FR';
        
        this.init();
    }
    
    async init() {
        try {
            // Charger les données du produit
            await this.loadProductData();
            
            // Initialiser la galerie d'images
            this.initImageGallery();
            
            // Charger les variantes si disponibles
            if (this.hasVariants()) {
                await this.loadVariants();
                this.renderVariantSelectors();
            }
            
            // Charger les méthodes de livraison
            await this.loadShippingMethods();
            
            // Attacher les événements
            this.attachEvents();
            
        } catch (error) {
            console.error('Erreur initialisation produit:', error);
        }
    }
    
    async loadProductData() {
        try {
            const response = await fetch(`/api/products/${this.productId}`);
            const data = await response.json();
            
            if (data.success) {
                this.product = data.product;
                this.images = data.product.images || [];
                return true;
            }
            return false;
        } catch (error) {
            console.error('Erreur chargement produit:', error);
            return false;
        }
    }
    
    async loadVariants() {
        try {
            const response = await fetch(`/api/variants/product/${this.productId}/summary`);
            const data = await response.json();
            
            if (data.success && data.summary.has_variants) {
                this.variants = data.summary.variants || [];
                this.variantSummary = data.summary;
                return true;
            }
            return false;
        } catch (error) {
            console.error('Erreur chargement variantes:', error);
            return false;
        }
    }
    
    async loadShippingMethods() {
        try {
            const response = await fetch(`/api/shipping/methods?country=${this.selectedCountry}`);
            const data = await response.json();
            
            if (data.success) {
                this.shippingMethods = data.methods || [];
                this.renderShippingOptions();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Erreur chargement livraison:', error);
            return false;
        }
    }
    
    // ==================== GALERIE D'IMAGES ====================
    
    initImageGallery() {
        if (!this.images || this.images.length === 0) {
            // Utiliser l'image par défaut du produit
            this.images = [this.product?.image_url || '/static/images/no-image.png'];
        }
        
        this.renderImageGallery();
    }
    
    renderImageGallery() {
        const mainImageContainer = document.getElementById('main-product-image');
        const thumbnailsContainer = document.getElementById('product-thumbnails');
        
        if (!mainImageContainer || !thumbnailsContainer) return;
        
        // Image principale
        mainImageContainer.innerHTML = `
            <div class="main-image-wrapper position-relative">
                <img src="${this.images[this.currentImageIndex]}" 
                     alt="Product" 
                     class="img-fluid rounded"
                     id="mainImage">
                <button class="btn btn-light position-absolute top-50 start-0 translate-middle-y ms-2" 
                        onclick="productManager.previousImage()" 
                        style="z-index: 10;">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <button class="btn btn-light position-absolute top-50 end-0 translate-middle-y me-2" 
                        onclick="productManager.nextImage()" 
                        style="z-index: 10;">
                    <i class="fas fa-chevron-right"></i>
                </button>
                <div class="position-absolute bottom-0 end-0 m-3">
                    <button class="btn btn-light btn-sm" onclick="productManager.zoomImage()">
                        <i class="fas fa-search-plus"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Miniatures
        thumbnailsContainer.innerHTML = this.images.map((img, index) => `
            <div class="thumbnail ${index === this.currentImageIndex ? 'active' : ''}" 
                 onclick="productManager.selectImage(${index})">
                <img src="${img}" alt="Thumbnail ${index + 1}" class="img-fluid rounded">
            </div>
        `).join('');
    }
    
    selectImage(index) {
        this.currentImageIndex = index;
        this.renderImageGallery();
    }
    
    previousImage() {
        this.currentImageIndex = (this.currentImageIndex - 1 + this.images.length) % this.images.length;
        this.renderImageGallery();
    }
    
    nextImage() {
        this.currentImageIndex = (this.currentImageIndex + 1) % this.images.length;
        this.renderImageGallery();
    }
    
    zoomImage() {
        const img = document.getElementById('mainImage');
        if (!img) return;
        
        // Créer modal de zoom
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl modal-dialog-centered">
                <div class="modal-content bg-dark">
                    <div class="modal-body p-0 position-relative">
                        <img src="${img.src}" class="img-fluid w-100">
                        <button type="button" class="btn-close btn-close-white position-absolute top-0 end-0 m-3" data-bs-dismiss="modal"></button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }
    
    // ==================== VARIANTES ====================
    
    hasVariants() {
        return this.product?.has_variants || false;
    }
    
    renderVariantSelectors() {
        const container = document.getElementById('variant-selectors');
        if (!container || !this.variantSummary) return;
        
        let html = '<div class="variant-options">';
        
        // Sélecteur de couleur
        if (this.variantSummary.colors && this.variantSummary.colors.length > 0) {
            html += `
                <div class="variant-group mb-4">
                    <label class="form-label fw-bold">Couleur:</label>
                    <div class="color-options d-flex flex-wrap gap-2">
                        ${this.variantSummary.colors.map(color => `
                            <button type="button" 
                                    class="btn btn-outline-primary color-btn" 
                                    data-color="${color}"
                                    onclick="productManager.selectColor('${color}')">
                                ${color}
                            </button>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Sélecteur de taille
        if (this.variantSummary.sizes && this.variantSummary.sizes.length > 0) {
            html += `
                <div class="variant-group mb-4">
                    <label class="form-label fw-bold">Taille:</label>
                    <div class="size-options d-flex flex-wrap gap-2" id="size-options">
                        ${this.variantSummary.sizes.map(size => `
                            <button type="button" 
                                    class="btn btn-outline-secondary size-btn" 
                                    data-size="${size}"
                                    onclick="productManager.selectSize('${size}')">
                                ${size}
                            </button>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    selectColor(color) {
        this.selectedColor = color;
        
        // Mettre à jour l'UI
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color === color);
        });
        
        // Filtrer les tailles disponibles
        this.updateAvailableSizes();
        
        // Mettre à jour la variante sélectionnée
        this.updateSelectedVariant();
    }
    
    selectSize(size) {
        this.selectedSize = size;
        
        // Mettre à jour l'UI
        document.querySelectorAll('.size-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.size === size);
        });
        
        // Mettre à jour la variante sélectionnée
        this.updateSelectedVariant();
    }
    
    updateAvailableSizes() {
        if (!this.selectedColor) return;
        
        const availableVariants = this.variants.filter(v => v.color === this.selectedColor);
        const availableSizes = [...new Set(availableVariants.map(v => v.size))];
        
        document.querySelectorAll('.size-btn').forEach(btn => {
            const size = btn.dataset.size;
            const isAvailable = availableSizes.includes(size);
            btn.disabled = !isAvailable;
            btn.classList.toggle('disabled', !isAvailable);
        });
    }
    
    updateSelectedVariant() {
        // Trouver la variante correspondante
        this.selectedVariant = this.variants.find(v => {
            const colorMatch = !this.selectedColor || v.color === this.selectedColor;
            const sizeMatch = !this.selectedSize || v.size === this.selectedSize;
            return colorMatch && sizeMatch;
        });
        
        if (this.selectedVariant) {
            // Mettre à jour le prix
            this.updatePrice(this.selectedVariant.price);
            
            // Mettre à jour le stock
            this.updateStock(this.selectedVariant.stock);
            
            // Mettre à jour l'image si disponible
            if (this.selectedVariant.image_url) {
                this.images[0] = this.selectedVariant.image_url;
                this.currentImageIndex = 0;
                this.renderImageGallery();
            }
        }
    }
    
    updatePrice(price) {
        const priceElement = document.getElementById('product-price');
        if (priceElement && price) {
            priceElement.innerHTML = `<span class="price-current" style="font-size: 2.5rem;">$${price.toFixed(2)}</span>`;
        }
    }
    
    updateStock(stock) {
        const stockElement = document.getElementById('stock-indicator');
        if (!stockElement) return;
        
        if (stock > 10) {
            stockElement.className = 'stock-indicator in-stock mb-3';
            stockElement.innerHTML = `
                <i class="fas fa-check-circle"></i>
                En stock (${stock} disponibles)
            `;
        } else if (stock > 0) {
            stockElement.className = 'stock-indicator low-stock mb-3';
            stockElement.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                Stock limité (${stock} restants)
            `;
        } else {
            stockElement.className = 'stock-indicator out-of-stock mb-3';
            stockElement.innerHTML = `
                <i class="fas fa-times-circle"></i>
                Rupture de stock
            `;
        }
    }
    
    // ==================== LIVRAISON ====================
    
    renderShippingOptions() {
        const container = document.getElementById('shipping-options');
        if (!container || !this.shippingMethods.length) return;
        
        container.innerHTML = `
            <div class="card-modern mt-4">
                <div class="card-modern-header">
                    <i class="fas fa-truck"></i> Options de livraison
                </div>
                <div class="card-modern-body">
                    ${this.shippingMethods.map(method => `
                        <div class="shipping-method d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                            <div>
                                <strong>${method.name}</strong>
                                <p class="mb-0 text-muted small">${method.delivery_time}</p>
                            </div>
                            <div class="text-end">
                                <strong class="text-primary">${method.price > 0 ? '$' + method.price.toFixed(2) : 'Gratuit'}</strong>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // ==================== PANIER ====================
    
    async addToCart() {
        const quantity = parseInt(document.getElementById('quantity')?.value || 1);
        
        // Vérifier si une variante doit être sélectionnée
        if (this.hasVariants() && !this.selectedVariant) {
            this.showNotification('Veuillez sélectionner toutes les options', 'warning');
            return;
        }
        
        try {
            const data = {
                product_id: this.productId,
                quantity: quantity
            };
            
            if (this.selectedVariant) {
                data.variant_id = this.selectedVariant.id;
            }
            
            const response = await fetch('/cart/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Produit ajouté au panier !', 'success');
                this.updateCartCount(result.cart_total);
            } else {
                this.showNotification(result.message || 'Erreur lors de l\'ajout', 'error');
            }
            
        } catch (error) {
            console.error('Erreur ajout au panier:', error);
            this.showNotification('Erreur lors de l\'ajout au panier', 'error');
        }
    }
    
    // ==================== UTILITAIRES ====================
    
    attachEvents() {
        // Bouton ajouter au panier
        const addToCartBtn = document.getElementById('add-to-cart-btn');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', () => this.addToCart());
        }
        
        // Sélecteur de pays pour livraison
        const countrySelect = document.getElementById('shipping-country');
        if (countrySelect) {
            countrySelect.addEventListener('change', (e) => {
                this.selectedCountry = e.target.value;
                this.loadShippingMethods();
            });
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'warning'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    updateCartCount(count) {
        const cartBadge = document.querySelector('.cart-count, .badge-cart');
        if (cartBadge) {
            cartBadge.textContent = count;
        }
    }
}

// Initialisation globale
let productManager = null;

document.addEventListener('DOMContentLoaded', function() {
    const productId = document.getElementById('product-id')?.value;
    if (productId) {
        productManager = new ProductDetailManager(productId);
    }
});

// Fonctions de quantité
function incrementQty() {
    const input = document.getElementById('quantity');
    const max = parseInt(input.max);
    const current = parseInt(input.value);
    if (current < max) {
        input.value = current + 1;
    }
}

function decrementQty() {
    const input = document.getElementById('quantity');
    const min = parseInt(input.min);
    const current = parseInt(input.value);
    if (current > min) {
        input.value = current - 1;
    }
}
