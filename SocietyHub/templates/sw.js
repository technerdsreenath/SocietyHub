/// <reference lib="webworker" />
/* eslint-env serviceworker */
/* global clients */

const CACHE_NAME = 'societyhub-pwa-v1';
const OFFLINE_URL = '/offline/';

const PRECACHE_ASSETS = [
    OFFLINE_URL,
    '/static/images/pwa-icon-192.png',
    '/static/images/badge-72.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/lucide@latest'
];

// 1. Install: Precache core shell and offline fallback
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS).catch((err) => {
                console.warn('[SW] Pre-caching warning:', err);
            });
        }).then(() => self.skipWaiting())
    );
});

// 2. Activate: Clear old caches and claim clients immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// 3. Fetch: Network-First for HTML navigation with offline page fallback
self.addEventListener('fetch', (event) => {
    const request = event.request;

    // Only handle GET requests
    if (request.method !== 'GET') return;

    // Handle HTML page navigation
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(() => {
                return caches.match(OFFLINE_URL);
            })
        );
        return;
    }

    // Static assets & images: Stale-While-Revalidate
    if (request.destination === 'image' || request.destination === 'style' || request.destination === 'script' || request.destination === 'font') {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                const fetchPromise = fetch(request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return networkResponse;
                }).catch(() => cachedResponse);

                return cachedResponse || fetchPromise;
            })
        );
    }
});

// 4. Push: Handle incoming Web Push Notifications
self.addEventListener('push', (event) => {
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data = { title: 'SocietyHub Notification', body: event.data.text() };
        }
    }

    const title = data.title || 'SocietyHub Notice';
    const options = {
        body: data.body || 'You have a new update from SocietyHub.',
        icon: data.icon || '/static/images/pwa-icon-192.png',
        badge: data.badge || '/static/images/badge-72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/dashboard/',
            timestamp: Date.now()
        },
        actions: data.actions || [
            { action: 'open', title: 'View Details' }
        ],
        tag: data.tag || 'societyhub-general',
        renotify: true
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// 5. Notification Click: Open or focus target URL
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/dashboard/';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            // Check if there is already a window open with this URL
            for (let client of windowClients) {
                if (client.url === targetUrl && 'focus' in client) {
                    return client.focus();
                }
            }
            // If any window open on this domain, navigate and focus it
            if (windowClients.length > 0 && 'focus' in windowClients[0] && 'navigate' in windowClients[0]) {
                return windowClients[0].navigate(targetUrl).then(client => client.focus());
            }
            // Otherwise open a new window
            if (self.clients.openWindow) {
                return self.clients.openWindow(targetUrl);
            }
        })
    );
});
