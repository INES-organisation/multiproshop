/**
 * Gestionnaire de variantes de produits
 * Gère la sélection de couleur/taille et la mise à jour du prix/stock
 */

class ProductVariantSelector {
    constructor(productId) {
        this.productId = productId;
        this.selectedColor = null;
        this.selectedSize = null;
        this.selectedVariant = null;
        this.variants = [];
        this.summary = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Charger le résumé des variantes
            await this.loadVariantsSummary();
            
            if (this.summary && this.summary.has_variants) {
                // Afficher les sélecteurs
                this.renderColorSelector();
                this.renderSizeSelector();
                
                // Attacher les événements
                this.attachEvents();
            }
        } catch (error) {
            console.error('Erreur initialisation variantes:', error);
        }
    }
    
    async loadVariantsSummary() {
        try {
            const response = await fetch(`/api/variants/product/${this.productId}/summary`);
            const data = await response.json();
            
            if (data.success) {
                this.summary = data.summary;
                this.variants = data.summary.variants || [];
                return true;
            }
            return false;
        } catch (error) {
            console.error('Erreur chargement variantes:', error);
            return false;
        }
    }
    
    renderColorSelector() {
        const container = document.getElementById('color-selector');
        if (!container || !this.summary.colors.length) return;
        
        container.innerHTML = `
            <div class="variant-option">
                <label class="variant-label">Couleur:</label>
                <div class="color-options">
                    ${this.summary.colors.map(color => `
                        <button type="button" 
                                class="color-option" 
                                data-color="${color}"
                                title="${color}">
                            <span class="color-name">${color}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    renderSizeSelector() {
        const container = document.getElementById('size-selector');
        if (!container || !this.summary.sizes.length) return;
        
        // Filtrer les tailles disponibles selon la couleur sélectionnée
        let availableSizes = this.summary.sizes;
        
        if (this.selectedColor) {
            const variantsForColor = this.variants.filter(v => v.color === this.selectedColor);
            availableSizes = [...new Set(variantsForColor.map(v => v.size))];
        }
        
        container.innerHTML = `
            <div class="variant-option">
                <label class="variant-label">Taille:</label>
                <div class="size-options">
                    ${availableSizes.map(size => `
                        <button type="button" 
                                class="size-option" 
                                data-size="${size}">
                            ${size}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    attachEvents() {
        // Événements couleur
        document.querySelectorAll('.color-option').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const color = e.currentTarget.dataset.color;
                this.selectColor(color);
            });
        });
        
        // Événements taille
        document.querySelectorAll('.size-option').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const size = e.currentTarget.dataset.size;
                this.selectSize(size);
            });
        });
    }
    
    selectColor(color) {
        // Mettre à jour la sélection
        this.selectedColor = color;
        
        // Mettre à jour l'UI
        document.querySelectorAll('.color-option').forEach(btn => {
            btn.classList.toggle('selected', btn.dataset.color === color);
        });
        
        // Réinitialiser la taille si elle n'est plus disponible
        if (this.selectedSize) {
            const variantsForColor = this.variants.filter(v => v.color === color);
            const sizesForColor = variantsForColor.map(v => v.size);
            
            if (!sizesForColor.includes(this.selectedSize)) {
                this.selectedSize = null;
            }
        }
        
        // Re-render le sélecteur de taille
        this.renderSizeSelector();
        this.attachEvents();
        
        // Mettre à jour la variante sélectionnée
        this.updateSelectedVariant();
    }
    
    selectSize(size) {
        // Mettre à jour la sélection
        this.selectedSize = size;
        
        // Mettre à jour l'UI
        document.querySelectorAll('.size-option').forEach(btn => {
            btn.classList.toggle('selected', btn.dataset.size === size);
        });
        
        // Mettre à jour la variante sélectionnée
        this.updateSelectedVariant();
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
                this.updateImage(this.selectedVariant.image_url);
            }
            
            // Activer le bouton d'ajout au panier
            this.enableAddToCart();
        } else {
            // Désactiver le bouton si sélection incomplète
            if (this.summary.colors.length > 0 && !this.selectedColor) {
                this.disableAddToCart('Veuillez sélectionner une couleur');
            } else if (this.summary.sizes.length > 0 && !this.selectedSize) {
                this.disableAddToCart('Veuillez sélectionner une taille');
            }
        }
    }
    
    updatePrice(price) {
        const priceElement = document.getElementById('product-price');
        if (priceElement && price) {
            priceElement.textContent = `$${price.toFixed(2)}`;
        }
    }
    
    updateStock(stock) {
        const stockElement = document.getElementById('product-stock');
        if (stockElement) {
            if (stock > 0) {
                stockElement.innerHTML = `<span class="text-success"><i class="bi bi-check-circle"></i> En stock (${stock})</span>`;
            } else {
                stockElement.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle"></i> Rupture de stock</span>`;
            }
        }
    }
    
    updateImage(imageUrl) {
        const mainImage = document.querySelector('.product-main-image img');
        if (mainImage) {
            mainImage.src = imageUrl;
        }
    }
    
    enableAddToCart() {
        const btn = document.getElementById('add-to-cart-btn');
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('disabled');
            
            // Mettre à jour le data-variant-id
            if (this.selectedVariant) {
                btn.dataset.variantId = this.selectedVariant.id;
            }
        }
    }
    
    disableAddToCart(message) {
        const btn = document.getElementById('add-to-cart-btn');
        if (btn) {
            btn.disabled = true;
            btn.classList.add('disabled');
            btn.title = message;
        }
    }
    
    getSelectedVariantId() {
        return this.selectedVariant ? this.selectedVariant.id : null;
    }
    
    hasVariants() {
        return this.summary && this.summary.has_variants;
    }
    
    isSelectionComplete() {
        if (!this.hasVariants()) return true;
        
        const needsColor = this.summary.colors.length > 0;
        const needsSize = this.summary.sizes.length > 0;
        
        return (!needsColor || this.selectedColor) && (!needsSize || this.selectedSize);
    }
}

// Fonction d'ajout au panier avec support variantes
async function addToCartWithVariant(productId, quantity = 1) {
    try {
        // Récupérer l'instance du sélecteur de variantes
        const variantSelector = window.productVariantSelector;
        
        let variantId = null;
        
        // Si le produit a des variantes, vérifier la sélection
        if (variantSelector && variantSelector.hasVariants()) {
            if (!variantSelector.isSelectionComplete()) {
                showNotification('Veuillez sélectionner toutes les options', 'warning');
                return;
            }
            variantId = variantSelector.getSelectedVariantId();
        }
        
        // Préparer les données
        const data = {
            product_id: productId,
            quantity: quantity
        };
        
        if (variantId) {
            data.variant_id = variantId;
        }
        
        // Envoyer la requête
        const response = await fetch('/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            
            // Mettre à jour le compteur du panier
            updateCartCount(result.cart_total);
        } else {
            showNotification(result.message, 'error');
        }
        
    } catch (error) {
        console.error('Erreur ajout au panier:', error);
        showNotification('Erreur lors de l\'ajout au panier', 'error');
    }
}

// Fonction pour afficher les notifications
function showNotification(message, type = 'info') {
    // Créer la notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'warning'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Supprimer après 3 secondes
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Fonction pour mettre à jour le compteur du panier
function updateCartCount(count) {
    const cartBadge = document.querySelector('.cart-count, .badge-cart');
    if (cartBadge) {
        cartBadge.textContent = count;
    }
}
