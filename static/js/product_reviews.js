/**
 * Gestionnaire d'avis produits CJ Dropshipping
 */

class ProductReviews {
    constructor(cjPid) {
        this.cjPid = cjPid;
        this.reviews = [];
        this.average = 0;
        this.total = 0;
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadReviews();
            this.renderReviews();
            this.renderRatingSummary();
        } catch (error) {
            console.error('Erreur initialisation avis:', error);
        }
    }
    
    async loadReviews() {
        try {
            const response = await fetch(`/api/cj/products/${this.cjPid}/reviews`);
            const data = await response.json();
            
            if (data.success) {
                this.reviews = data.reviews;
                this.average = data.average;
                this.total = data.total;
                return true;
            }
            return false;
        } catch (error) {
            console.error('Erreur chargement avis:', error);
            return false;
        }
    }
    
    renderReviews() {
        const container = document.getElementById('reviews-list');
        if (!container) return;
        
        if (this.reviews.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    Aucun avis pour le moment. Soyez le premier à donner votre avis !
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.reviews.map(review => `
            <div class="review-item">
                <div class="review-header">
                    <div>
                        <div class="reviewer-name">
                            ${review.author}
                            ${review.verified ? '<span class="badge bg-success ms-2"><i class="fas fa-check"></i> Achat vérifié</span>' : ''}
                        </div>
                        <div class="product-rating-modern">
                            ${this.renderStars(review.rating)}
                        </div>
                    </div>
                    <div class="review-date">${review.date}</div>
                </div>
                <p class="review-comment">${review.comment}</p>
                ${review.images && review.images.length > 0 ? `
                    <div class="review-images">
                        ${review.images.map(img => `
                            <img src="${img}" alt="Photo avis" class="review-image" onclick="window.open('${img}', '_blank')">
                        `).join('')}
                    </div>
                ` : ''}
                <div class="review-footer">
                    <button class="btn-helpful" onclick="window.productReviews.markHelpful(${review.id})">
                        <i class="far fa-thumbs-up"></i>
                        Utile (${review.helpful})
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    renderRatingSummary() {
        const container = document.getElementById('rating-summary');
        if (!container) return;
        
        container.innerHTML = `
            <div class="card-modern">
                <div class="card-modern-header">
                    Note moyenne
                </div>
                <div class="card-modern-body text-center">
                    <div class="rating-average">${this.average}</div>
                    <div class="product-rating-modern justify-content-center mb-2">
                        ${this.renderStars(this.average)}
                    </div>
                    <p class="text-muted mb-0">Basé sur ${this.total} avis</p>
                </div>
            </div>
        `;
        
        // Mettre à jour le compteur dans l'onglet
        const tabReviews = document.querySelector('.tab-modern:has(i.fa-star)');
        if (tabReviews) {
            tabReviews.innerHTML = `<i class="fas fa-star"></i> Avis (${this.total})`;
        }
    }
    
    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        
        let stars = '';
        
        // Étoiles pleines
        for (let i = 0; i < fullStars; i++) {
            stars += '<i class="fas fa-star"></i>';
        }
        
        // Demi-étoile
        if (hasHalfStar) {
            stars += '<i class="fas fa-star-half-alt"></i>';
        }
        
        // Étoiles vides
        for (let i = 0; i < emptyStars; i++) {
            stars += '<i class="far fa-star"></i>';
        }
        
        return stars;
    }
    
    async markHelpful(reviewId) {
        try {
            // TODO: Implémenter l'API pour marquer un avis comme utile
            console.log('Avis marqué comme utile:', reviewId);
            
            // Mettre à jour l'UI
            const review = this.reviews.find(r => r.id === reviewId);
            if (review) {
                review.helpful++;
                this.renderReviews();
            }
        } catch (error) {
            console.error('Erreur mark helpful:', error);
        }
    }
    
    async loadMoreReviews() {
        // TODO: Implémenter la pagination
        console.log('Chargement de plus d\'avis...');
    }
}

// Fonction pour initialiser les avis
function initProductReviews(cjPid) {
    if (!cjPid) {
        console.warn('CJ PID manquant pour les avis');
        return null;
    }
    
    window.productReviews = new ProductReviews(cjPid);
    return window.productReviews;
}
