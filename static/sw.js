const CACHE_NAME = 'splash-rc-v2';
const ASSETS_TO_CACHE = [
    '/',
    '/img/logo.ico',
    '/portaria/',
    '/portaria/visitantes/',
    '/portaria/encomendas/',
    '/portaria/solicitacoes/',
    '/sindico/visitantes/',
    '/sindico/encomendas/',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
];

// Install: cache essential assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

// Activate: clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys
                .filter(key => key !== CACHE_NAME)
                .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch: network-first strategy (fall back to cache for offline)
self.addEventListener('fetch', event => {
    // By-pass cache on sensitive auth and admin paths independent of HTTP method
    const bypassRoutes = ['/login', '/logout', '/admin', '/password_reset', '/reset', '/api/', '/sindico/', '/morador/'];
    if (bypassRoutes.some(route => event.request.url.includes(route))) {
        event.respondWith(fetch(event.request)); // Vai direto para a rede, ignora o cache
        return;
    }

    // Skip non-GET requests for the rest
    if (event.request.method !== 'GET') return;

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Cache successful responses
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, clone);
                });
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});

// Push notification listener
self.addEventListener('push', event => {
    let data = {};
    try {
        if (event.data) {
            data = event.data.json();
        }
    } catch (e) {
        data = { titulo: 'Notificação', mensagem: event.data.text() };
    }
    
    const titulo = data.titulo || "Notificação do Condomínio";
    const mensagem = data.mensagem || data.body || "Você tem uma nova atualização.";
    const url = data.url || "/";

    event.waitUntil(
        self.registration.showNotification(titulo, {
            body: mensagem,
            icon: '/static/img/icon-192.png',
            badge: '/static/img/icon-192.png',
            data: { url: url }
        })
    );
});

// Handle notification click
self.addEventListener('notificationclick', event => {
    event.notification.close();
    const urlToOpen = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
            for (let i = 0; i < windowClients.length; i++) {
                let client = windowClients[i];
                if (client.url.includes(urlToOpen) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});
