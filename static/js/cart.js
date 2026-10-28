/**
 * Gestion du panier - AJAX
 */

// Ajouter un produit au panier
function addToCart(productId, quantity = 1, variantId = null) {
    const payload = {product_id: productId, quantity: quantity};
    if (variantId) {
        payload.variant_id = variantId;
    }
    fetch('/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            updateCartCounter(data.cart_total);
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Une erreur est survenue', 'error');
    });
}

// Mettre à jour la quantité d'un produit
function updateQuantity(cartKey, change) {
    // Récupérer la quantité actuelle via data-cart-key
    const qtyInput = document.querySelector(`input[data-cart-key="${cartKey}"]`);
    if (!qtyInput) {
        console.error('Input non trouvé pour cart_key:', cartKey);
        return;
    }
    const currentQty = parseInt(qtyInput.value);
    const newQty = currentQty + change;
    
    if (newQty < 1) {
        removeItem(cartKey);
        return;
    }
    
    fetch(`/cart/update/${cartKey}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            quantity: newQty
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Recharger la page pour mettre à jour l'affichage
            location.reload();
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Une erreur est survenue', 'error');
    });
}

// Supprimer un produit du panier
function removeItem(cartKey) {
    if (!confirm('Voulez-vous vraiment supprimer cet article ?')) {
        return;
    }
    
    fetch(`/cart/remove/${cartKey}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // Recharger la page
            location.reload();
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Une erreur est survenue', 'error');
    });
}

// Vider le panier
function clearCart() {
    if (!confirm('Voulez-vous vraiment vider votre panier ?')) {
        return;
    }
    
    fetch('/cart/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            location.reload();
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Une erreur est survenue', 'error');
    });
}

// Mettre à jour le compteur du panier dans le header
function updateCartCounter(count) {
    const cartBadge = document.querySelector('.cart-badge');
    const cartCount = document.querySelector('.cart-count');
    
    if (cartBadge) {
        cartBadge.textContent = count;
        if (count > 0) {
            cartBadge.style.display = 'inline-block';
        } else {
            cartBadge.style.display = 'none';
        }
    }
    
    if (cartCount) {
        cartCount.textContent = count;
    }
}

// Charger le compteur du panier au chargement de la page
function loadCartCount() {
    fetch('/cart/count')
        .then(response => response.json())
        .then(data => {
            updateCartCounter(data.total_items);
        })
        .catch(error => {
            console.error('Erreur lors du chargement du compteur:', error);
        });
}

// Afficher une notification
function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Ajouter au body
    document.body.appendChild(notification);
    
    // Afficher avec animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Masquer après 3 secondes
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    loadCartCount();
    
    // Ajouter les styles pour les notifications
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 9999;
                transform: translateX(400px);
                transition: transform 0.3s ease;
                max-width: 400px;
            }
            
            .notification.show {
                transform: translateX(0);
            }
            
            .notification-content {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            
            .notification-content i {
                font-size: 1.5rem;
            }
            
            .notification-success {
                border-left: 4px solid #10b981;
            }
            
            .notification-success i {
                color: #10b981;
            }
            
            .notification-error {
                border-left: 4px solid #ef4444;
            }
            
            .notification-error i {
                color: #ef4444;
            }
            
            .notification-info {
                border-left: 4px solid #3b82f6;
            }
            
            .notification-info i {
                color: #3b82f6;
            }
        `;
        document.head.appendChild(style);
    }
});
