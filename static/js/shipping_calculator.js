/**
 * Calculateur de frais de livraison CJ Dropshipping
 */

class ShippingCalculator {
    constructor(productId, defaultCountry = 'FR') {
        this.productId = productId;
        this.selectedCountry = defaultCountry;
        this.shippingMethods = [];
        this.selectedMethod = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Charger les pays disponibles
            await this.loadCountries();
            
            // Calculer les frais pour le pays par défaut
            await this.calculateShipping();
            
            // Afficher les options
            this.renderShippingOptions();
        } catch (error) {
            console.error('Erreur initialisation shipping:', error);
        }
    }
    
    async loadCountries() {
        try {
            const response = await fetch('/api/cj/shipping/countries');
            const data = await response.json();
            
            if (data.success) {
                this.countries = data.countries;
                this.renderCountrySelector();
            }
        } catch (error) {
            console.error('Erreur chargement pays:', error);
        }
    }
    
    renderCountrySelector() {
        const container = document.getElementById('shipping-country-selector');
        if (!container) return;
        
        container.innerHTML = `
            <div class="shipping-country-select">
                <label for="shipping-country">Livraison vers :</label>
                <select id="shipping-country" class="form-select">
                    ${this.countries.map(country => `
                        <option value="${country.code}" ${country.code === this.selectedCountry ? 'selected' : ''}>
                            ${country.name}
                        </option>
                    `).join('')}
                </select>
            </div>
        `;
        
        // Événement changement de pays
        document.getElementById('shipping-country').addEventListener('change', (e) => {
            this.selectedCountry = e.target.value;
            this.calculateShipping();
        });
    }
    
    async calculateShipping() {
        try {
            const response = await fetch('/api/cj/shipping/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    product_id: this.productId,
                    country: this.selectedCountry,
                    quantity: this.getQuantity()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.shippingMethods = data.methods;
                this.renderShippingOptions();
            } else {
                this.showError('Impossible de calculer les frais de livraison');
            }
        } catch (error) {
            console.error('Erreur calcul shipping:', error);
            this.showError('Erreur lors du calcul des frais de livraison');
        }
    }
    
    renderShippingOptions() {
        const container = document.getElementById('shipping-options');
        if (!container) return;
        
        if (this.shippingMethods.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    Frais de livraison calculés au checkout
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="shipping-options-container">
                <h5 class="shipping-title">
                    <i class="fas fa-truck"></i> Options de livraison
                </h5>
                <div class="shipping-methods">
                    ${this.shippingMethods.map((method, index) => `
                        <div class="shipping-method ${index === 0 ? 'selected' : ''}" 
                             data-method-code="${method.code}"
                             onclick="window.shippingCalculator.selectMethod('${method.code}')">
                            <div class="method-info">
                                <div class="method-name">
                                    <i class="fas fa-shipping-fast"></i>
                                    ${method.name}
                                </div>
                                <div class="method-time text-muted">
                                    <i class="far fa-clock"></i>
                                    ${method.delivery_time}
                                </div>
                                ${method.description ? `
                                    <div class="method-description text-muted">
                                        ${method.description}
                                    </div>
                                ` : ''}
                            </div>
                            <div class="method-price">
                                ${method.price === 0 ? 
                                    '<span class="badge bg-success">GRATUIT</span>' : 
                                    `<strong>$${method.price.toFixed(2)}</strong>`
                                }
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Sélectionner la première méthode par défaut
        if (this.shippingMethods.length > 0) {
            this.selectedMethod = this.shippingMethods[0];
        }
    }
    
    selectMethod(methodCode) {
        // Trouver la méthode
        this.selectedMethod = this.shippingMethods.find(m => m.code === methodCode);
        
        // Mettre à jour l'UI
        document.querySelectorAll('.shipping-method').forEach(el => {
            el.classList.toggle('selected', el.dataset.methodCode === methodCode);
        });
        
        // Émettre un événement
        document.dispatchEvent(new CustomEvent('shipping-method-selected', {
            detail: this.selectedMethod
        }));
    }
    
    getQuantity() {
        const qtyInput = document.getElementById('quantity');
        return qtyInput ? parseInt(qtyInput.value) : 1;
    }
    
    getSelectedMethod() {
        return this.selectedMethod;
    }
    
    showError(message) {
        const container = document.getElementById('shipping-options');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${message}
                </div>
            `;
        }
    }
}

// Fonction pour initialiser le calculateur
function initShippingCalculator(productId, country = 'FR') {
    window.shippingCalculator = new ShippingCalculator(productId, country);
    return window.shippingCalculator;
}
