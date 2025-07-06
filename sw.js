/**
 * Service Worker for 차계부 프로그램
 * Provides caching, offline functionality, and performance optimizations
 */

const CACHE_NAME = 'car-expense-tracker-v1.0.0';
const STATIC_CACHE_NAME = 'static-v1.0.0';
const RUNTIME_CACHE_NAME = 'runtime-v1.0.0';

// Performance: Critical resources to cache immediately
const CRITICAL_RESOURCES = [
    '/',
    '/index.html',
    '/app.js',
    '/styles.css',
    '/manifest.json'
];

// Performance: External resources to cache on runtime
const RUNTIME_CACHE_URLS = [
    'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js',
    'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap'
];

// Cache strategy configuration
const CACHE_STRATEGIES = {
    fonts: {
        cacheName: 'fonts-v1',
        maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
        maxEntries: 10
    },
    libraries: {
        cacheName: 'libraries-v1',
        maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
        maxEntries: 20
    },
    static: {
        cacheName: STATIC_CACHE_NAME,
        maxAge: 24 * 60 * 60 * 1000, // 1 day
        maxEntries: 50
    }
};

/**
 * Install Event - Cache critical resources
 */
self.addEventListener('install', event => {
    console.log('[ServiceWorker] Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('[ServiceWorker] Caching critical resources');
                return cache.addAll(CRITICAL_RESOURCES);
            })
            .then(() => {
                console.log('[ServiceWorker] Installation complete');
                return self.skipWaiting(); // Force activate immediately
            })
            .catch(error => {
                console.error('[ServiceWorker] Installation failed:', error);
            })
    );
});

/**
 * Activate Event - Clean up old caches
 */
self.addEventListener('activate', event => {
    console.log('[ServiceWorker] Activating...');
    
    event.waitUntil(
        Promise.all([
            cleanupOldCaches(),
            self.clients.claim() // Take control of all pages immediately
        ])
    );
});

/**
 * Fetch Event - Handle network requests with caching strategies
 */
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension and other non-http requests
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // Apply caching strategy based on resource type
    event.respondWith(handleRequest(request));
});

/**
 * Handle different types of requests with appropriate caching strategies
 */
async function handleRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Strategy 1: Cache First for static assets
        if (isCriticalResource(request)) {
            return await cacheFirst(request, STATIC_CACHE_NAME);
        }
        
        // Strategy 2: Network First for API calls (if any)
        if (isApiRequest(url)) {
            return await networkFirst(request, RUNTIME_CACHE_NAME);
        }
        
        // Strategy 3: Stale While Revalidate for external libraries
        if (isExternalLibrary(url)) {
            return await staleWhileRevalidate(request, CACHE_STRATEGIES.libraries.cacheName);
        }
        
        // Strategy 4: Cache First for fonts
        if (isFontRequest(url)) {
            return await cacheFirst(request, CACHE_STRATEGIES.fonts.cacheName);
        }
        
        // Strategy 5: Network Only for other requests
        return await fetch(request);
        
    } catch (error) {
        console.error('[ServiceWorker] Request failed:', error);
        
        // Fallback for critical resources
        if (isCriticalResource(request)) {
            return await getFromCache(request) || await createOfflineFallback();
        }
        
        throw error;
    }
}

/**
 * Cache First Strategy - Check cache first, then network
 */
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        // Performance: Return cached version immediately
        return cachedResponse;
    }
    
    // Fallback to network
    const networkResponse = await fetch(request);
    
    // Cache the response for future use
    if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
}

/**
 * Network First Strategy - Try network first, fallback to cache
 */
async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Performance: Update cache in background
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        // Fallback to cache
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        throw error;
    }
}

/**
 * Stale While Revalidate Strategy - Return cache immediately, update in background
 */
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    // Performance: Update cache in background without waiting
    const updateCache = async () => {
        try {
            const networkResponse = await fetch(request);
            if (networkResponse.ok) {
                await cache.put(request, networkResponse.clone());
            }
        } catch (error) {
            console.warn('[ServiceWorker] Background update failed:', error);
        }
    };
    
    // Don't wait for the cache update
    updateCache();
    
    // Return cached version immediately if available
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // If no cache, wait for network
    return await fetch(request);
}

/**
 * Get response from any cache
 */
async function getFromCache(request) {
    const cacheNames = await caches.keys();
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const response = await cache.match(request);
        
        if (response) {
            return response;
        }
    }
    
    return null;
}

/**
 * Create offline fallback page
 */
async function createOfflineFallback() {
    return new Response(`
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>오프라인 - 차계부 프로그램</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    text-align: center; 
                    padding: 50px; 
                    background: #f5f5f5;
                }
                .container {
                    max-width: 400px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #00796b; margin-bottom: 20px; }
                p { color: #666; line-height: 1.6; }
                button {
                    background: #00796b;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 20px;
                }
                button:hover { background: #004d40; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚗 차계부 프로그램</h1>
                <p>현재 인터넷 연결이 없습니다.</p>
                <p>저장된 데이터는 브라우저에 안전하게 보관되어 있으며, 연결이 복구되면 모든 기능을 사용할 수 있습니다.</p>
                <button onclick="window.location.reload()">다시 시도</button>
            </div>
        </body>
        </html>
    `, {
        headers: { 'Content-Type': 'text/html' }
    });
}

/**
 * Clean up old caches to free up storage
 */
async function cleanupOldCaches() {
    const cacheWhitelist = [
        STATIC_CACHE_NAME,
        RUNTIME_CACHE_NAME,
        ...Object.values(CACHE_STRATEGIES).map(strategy => strategy.cacheName)
    ];
    
    const cacheNames = await caches.keys();
    
    return Promise.all(
        cacheNames.map(cacheName => {
            if (!cacheWhitelist.includes(cacheName)) {
                console.log('[ServiceWorker] Deleting old cache:', cacheName);
                return caches.delete(cacheName);
            }
        })
    );
}

/**
 * Clean up cache entries that exceed max age or max entries
 */
async function cleanupCache(cacheName, maxAge, maxEntries) {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();
    
    if (requests.length <= maxEntries) {
        return;
    }
    
    // Sort by cache time and remove oldest entries
    const entries = await Promise.all(
        requests.map(async request => {
            const response = await cache.match(request);
            const cacheTime = new Date(response.headers.get('date') || 0).getTime();
            return { request, cacheTime };
        })
    );
    
    entries.sort((a, b) => a.cacheTime - b.cacheTime);
    
    const entriesToDelete = entries.slice(0, entries.length - maxEntries);
    
    return Promise.all(
        entriesToDelete.map(entry => cache.delete(entry.request))
    );
}

/**
 * Background sync for deferred actions (future enhancement)
 */
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Future: Sync offline actions when connection is restored
    console.log('[ServiceWorker] Background sync triggered');
}

/**
 * Message handling for communication with main app
 */
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// Helper functions for request classification
function isCriticalResource(request) {
    const url = new URL(request.url);
    return CRITICAL_RESOURCES.some(resource => url.pathname.endsWith(resource));
}

function isApiRequest(url) {
    // Future: Add API endpoint detection
    return url.pathname.startsWith('/api/');
}

function isExternalLibrary(url) {
    return RUNTIME_CACHE_URLS.some(cacheUrl => url.href.startsWith(cacheUrl.split('?')[0]));
}

function isFontRequest(url) {
    return url.hostname === 'fonts.googleapis.com' || 
           url.hostname === 'fonts.gstatic.com' ||
           url.pathname.includes('fonts');
}

// Performance monitoring
self.addEventListener('fetch', event => {
    // Future: Add performance metrics collection
});

console.log('[ServiceWorker] Script loaded successfully');