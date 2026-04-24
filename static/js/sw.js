/**
 * Service Worker pour MultiProShop
 * Cache les ressources pour un chargement instantané
 */

const CACHE_NAME = 'multiproshop-v1';
const CACHE_VERSION = '1.0.0';

// Ressources à mettre en cache immédiatement
const urlsToCache = [
  '/',
  '/static/css/styles.css',
  '/static/css/layout_modern.css',
  '/static/js/cart.js',
  '/static/images/mps.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css'
];

// Installation du Service Worker
self.addEventListener('install', event => {
  console.log('[SW] Installation...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Mise en cache des ressources');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activation du Service Worker
self.addEventListener('activate', event => {
  console.log('[SW] Activation...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Suppression ancien cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Stratégie de cache : Cache First, puis Network
self.addEventListener('fetch', event => {
  const { request } = event;
  
  // Ignorer les requêtes non-GET
  if (request.method !== 'GET') {
    return;
  }
  
  // Ignorer les requêtes admin et API
  if (request.url.includes('/admin') || request.url.includes('/api/')) {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        // Si en cache, retourner immédiatement
        if (cachedResponse) {
          // Mettre à jour en arrière-plan
          fetch(request).then(networkResponse => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then(cache => {
                cache.put(request, networkResponse.clone());
              });
            }
          }).catch(() => {});
          
          return cachedResponse;
        }
        
        // Sinon, récupérer du réseau et mettre en cache
        return fetch(request).then(networkResponse => {
          // Vérifier si la réponse est valide
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type === 'error') {
            return networkResponse;
          }
          
          // Cloner la réponse
          const responseToCache = networkResponse.clone();
          
          // Mettre en cache les ressources statiques
          if (request.url.includes('/static/') || 
              request.url.includes('cdn.jsdelivr.net') ||
              request.url.includes('cdnjs.cloudflare.com')) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, responseToCache);
            });
          }
          
          return networkResponse;
        }).catch(() => {
          // En cas d'erreur réseau, retourner une page offline si disponible
          return caches.match('/offline.html');
        });
      })
  );
});

// Gestion des messages
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => caches.delete(cacheName))
        );
      }).then(() => {
        console.log('[SW] Cache vidé');
      })
    );
  }
});

console.log('[SW] Service Worker chargé - Version', CACHE_VERSION);
