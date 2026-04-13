const CACHE_NAME = 'splash-rc-v3'; // Versão 3 para forçar o navegador a atualizar
const ASSETS_TO_CACHE = [
    '/',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
];

// Install: Faz o cache de forma inteligente (se um falhar, não quebra o resto)
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return Promise.all(
                ASSETS_TO_CACHE.map(url => {
                    return fetch(url).then(response => {
                        if (!response.ok) throw new TypeError('Falha ao baixar ' + url);
                        return cache.put(url, response);
                    }).catch(err => console.warn('Página ignorada no cache offline:', url));
                })
            );
        }).then(() => self.skipWaiting())
    );
});

// Activate: Limpa os caches velhos
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

// Fetch: network-first strategy
self.addEventListener('fetch', event => {
    const bypassRoutes = ['/login', '/logout', '/admin', '/password_reset', '/reset', '/api/', '/sindico/', '/morador/', '/portaria/'];
    if (bypassRoutes.some(route => event.request.url.includes(route))) {
        event.respondWith(fetch(event.request)); 
        return;
    }

    if (event.request.method !== 'GET') return;

    event.respondWith(
        fetch(event.request)
            .then(response => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});

// A CASA DAS MÁQUINAS: Receptor do Push Notification
self.addEventListener('push', event => {
    let data = {};
    try {
        if (event.data) {
            data = event.data.json();
        }
    } catch (e) {
        data = { titulo: 'Notificação', mensagem: event.data.text() };
    }
    
    const titulo = data.titulo || "KS Tech - Condomínio";
    const mensagem = data.mensagem || data.body || "Você tem um novo aviso no painel.";
    const url = data.link || data.url || "/";

    event.waitUntil(
        self.registration.showNotification(titulo, {
            body: mensagem,
            icon: '/static/img/icon-192.png',
            badge: '/static/img/icon-192.png',
            vibrate: [200, 100, 200, 100, 200], // Vibração tática
            data: { url: url }
        })
    );
});

// O Gatilho do Clique: Abre a tela certa quando o morador clica no aviso
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