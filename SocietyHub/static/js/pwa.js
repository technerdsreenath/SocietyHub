/**
 * SocietyHub Progressive Web Application (PWA) & Web Push Manager
 */

/**
 * Modern Floating Toast Notification System
 * @param {string} message - Message text to display
 * @param {'success'|'error'|'warning'|'info'} type - Toast aesthetic style
 * @param {number} duration - Auto-dismiss timeout in ms
 */
window.showToast = function(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none max-w-sm w-full px-4 sm:px-0';
        document.body.appendChild(container);
    }

    const config = {
        success: {
            bg: 'bg-emerald-50 border-emerald-200 text-emerald-950',
            icon: 'check-circle-2',
            iconColor: 'text-emerald-600',
        },
        error: {
            bg: 'bg-rose-50 border-rose-200 text-rose-950',
            icon: 'alert-triangle',
            iconColor: 'text-rose-600',
        },
        warning: {
            bg: 'bg-amber-50 border-amber-200 text-amber-950',
            icon: 'alert-circle',
            iconColor: 'text-amber-600',
        },
        info: {
            bg: 'bg-slate-50 border-slate-200 text-slate-950',
            icon: 'info',
            iconColor: 'text-portal-primary',
        }
    }[type] || {
        bg: 'bg-slate-50 border-slate-200 text-slate-950',
        icon: 'info',
        iconColor: 'text-portal-primary',
    };

    const toast = document.createElement('div');
    toast.className = `pointer-events-auto flex items-start gap-3 p-3.5 rounded-2xl border shadow-lg backdrop-blur-md transition-all duration-300 transform -translate-y-2 opacity-0 ${config.bg}`;
    toast.innerHTML = `
        <div class="w-7 h-7 rounded-xl flex items-center justify-center shrink-0 ${config.iconColor} bg-white/80 shadow-xs">
            <i data-lucide="${config.icon}" class="w-4 h-4"></i>
        </div>
        <div class="flex-1 text-xs leading-relaxed font-medium pt-1">
            ${message}
        </div>
        <button type="button" class="text-slate-400 hover:text-slate-700 transition-colors p-1 cursor-pointer shrink-0" onclick="this.parentElement.remove()">
            <i data-lucide="x" class="w-3.5 h-3.5"></i>
        </button>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    // Enter animation
    requestAnimationFrame(() => {
        toast.classList.remove('-translate-y-2', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
    });

    // Auto dismiss
    setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', '-translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, duration);
};

function urlB64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    if (cookieValue) return cookieValue;
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenInput ? tokenInput.value : '';
}

let swRegistration = null;
let deferredInstallPrompt = null;

// 1. Service Worker Registration & iOS Detection
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then((registration) => {
                swRegistration = registration;
                console.log('[PWA] Service Worker registered for scope:', registration.scope);
                updateNotificationUI();
            })
            .catch((err) => {
                console.error('[PWA] Service Worker registration failed:', err);
            });
        
        checkIOSSafari();
    });
}

function checkIOSSafari() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isStandalone = window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches;
    const iosNotice = document.getElementById('ios-push-notice');
    if (isIOS && !isStandalone && iosNotice) {
        iosNotice.classList.remove('hidden');
    }
}

// 2. PWA Install Prompt Capture & Banner Management
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    const installBtn = document.getElementById('pwa-install-btn');
    const installBanner = document.getElementById('pwa-install-banner');
    if (installBtn) installBtn.classList.remove('hidden');
    if (installBanner && !sessionStorage.getItem('pwa_banner_dismissed')) {
        installBanner.classList.remove('hidden');
    }
});

window.addEventListener('appinstalled', () => {
    console.log('[PWA] SocietyHub was successfully installed');
    deferredInstallPrompt = null;
    const installBtn = document.getElementById('pwa-install-btn');
    const installBanner = document.getElementById('pwa-install-banner');
    if (installBtn) installBtn.classList.add('hidden');
    if (installBanner) installBanner.classList.add('hidden');
    showToast('SocietyHub was added to your device Home Screen!', 'success');
});

window.triggerPWAInstall = async function() {
    if (!deferredInstallPrompt) {
        showToast('SocietyHub is already installed or your browser added it to your home screen.', 'info');
        return;
    }
    deferredInstallPrompt.prompt();
    const { outcome } = await deferredInstallPrompt.userChoice;
    console.log('[PWA] Install prompt outcome:', outcome);
    deferredInstallPrompt = null;
    const installBtn = document.getElementById('pwa-install-btn');
    const installBanner = document.getElementById('pwa-install-banner');
    if (installBtn) installBtn.classList.add('hidden');
    if (installBanner) installBanner.classList.add('hidden');
};

window.dismissPWAInstallBanner = function() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.classList.add('hidden');
        sessionStorage.setItem('pwa_banner_dismissed', 'true');
    }
};

// 3. Notification Status & Subscription Management
async function updateNotificationUI() {
    const bellBadge = document.getElementById('push-status-badge');
    const statusText = document.getElementById('push-status-text');
    const toggleBtn = document.getElementById('push-toggle-btn');

    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
        if (statusText) statusText.innerText = 'Not Supported';
        return;
    }

    if (!swRegistration) {
        try {
            swRegistration = await navigator.serviceWorker.ready;
        } catch (e) {
            return;
        }
    }

    const sub = await swRegistration.pushManager.getSubscription();
    const isGranted = (Notification.permission === 'granted' && !!sub);

    if (bellBadge) {
        if (isGranted) {
            bellBadge.className = 'w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-white animate-pulse';
        } else {
            bellBadge.className = 'w-2 h-2 rounded-full bg-amber-400 ring-2 ring-white';
        }
    }

    if (statusText) {
        statusText.innerText = isGranted ? 'Push Notifications Active' : (Notification.permission === 'denied' ? 'Notifications Blocked' : 'Notifications Paused');
        statusText.className = isGranted ? 'text-[11px] font-bold text-emerald-700' : 'text-[11px] font-bold text-amber-700';
    }

    const footerDot = document.getElementById('push-footer-dot');
    if (footerDot) {
        footerDot.className = isGranted ? 'w-2 h-2 rounded-full bg-emerald-500' : 'w-2 h-2 rounded-full bg-amber-400';
    }

    if (toggleBtn) {
        if (isGranted) {
            toggleBtn.innerHTML = '<i data-lucide="bell-off" class="w-3.5 h-3.5 mr-1.5"></i> Mute Notifications';
            toggleBtn.className = 'w-full py-2 px-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl text-xs font-bold transition-all flex items-center justify-center cursor-pointer';
        } else {
            toggleBtn.innerHTML = '<i data-lucide="bell" class="w-3.5 h-3.5 mr-1.5"></i> Enable Push Notifications';
            toggleBtn.className = 'w-full py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center shadow-xs cursor-pointer';
        }
        if (window.lucide) lucide.createIcons();
    }
}

window.togglePushNotifications = async function() {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) {
        showToast('Push Notifications are not supported by this browser.', 'warning');
        return;
    }

    if (!swRegistration) {
        swRegistration = await navigator.serviceWorker.ready;
    }

    const currentSub = await swRegistration.pushManager.getSubscription();

    if (currentSub) {
        // Unsubscribe
        try {
            await currentSub.unsubscribe();
            await fetch('/api/push/unsubscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ endpoint: currentSub.endpoint })
            });
            showToast('Push notifications muted on this device.', 'info');
        } catch (e) {
            console.error('[PWA] Failed to unsubscribe:', e);
            showToast('Failed to mute notifications.', 'error');
        }
        updateNotificationUI();
        return;
    }

    // Subscribe Flow
    try {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            showToast('Notification permission was not granted by browser settings.', 'warning');
            updateNotificationUI();
            return;
        }

        const vapidRes = await fetch('/api/push/vapid-key/');
        const { publicKey } = await vapidRes.json();
        if (!publicKey) {
            showToast('VAPID public key not found on server.', 'error');
            return;
        }

        const applicationServerKey = urlB64ToUint8Array(publicKey);
        const newSub = await swRegistration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
        });

        // Send to backend
        const saveRes = await fetch('/api/push/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(newSub)
        });

        const saveJson = await saveRes.json();
        if (saveJson.status === 'success') {
            showToast('Push notifications enabled! You will receive live society updates.', 'success');
        } else {
            showToast('Failed to register subscription: ' + saveJson.message, 'error');
        }
    } catch (err) {
        console.error('[PWA] Push subscription error:', err);
        showToast('Failed to enable push: ' + err.message, 'error');
    }

    updateNotificationUI();
};

window.sendTestPush = async function() {
    const btn = document.getElementById('test-push-btn');
    if (btn) btn.disabled = true;

    try {
        const res = await fetch('/api/push/test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        const json = await res.json();
        if (json.status === 'success') {
            showToast(json.message, 'success');
        } else if (json.status === 'warning') {
            showToast(json.message, 'warning');
            window.togglePushNotifications();
        } else {
            showToast('Error: ' + json.message, 'error');
        }
    } catch (e) {
        showToast('Network request failed: ' + e.message, 'error');
    } finally {
        if (btn) btn.disabled = false;
        updateNotificationUI();
    }
};

// =========================================================
// 4. Real-Time In-App Notification Engine & Notification Center
// =========================================================

let lastSeenNotificationId = 0;
let isFirstPoll = true;

const NOTIF_ICONS = {
    bill: { icon: 'receipt', color: 'text-amber-600', bg: 'bg-amber-100', border: 'border-amber-200' },
    notice: { icon: 'megaphone', color: 'text-indigo-600', bg: 'bg-indigo-100', border: 'border-indigo-200' },
    report: { icon: 'file-text', color: 'text-emerald-600', bg: 'bg-emerald-100', border: 'border-emerald-200' },
    complaint: { icon: 'wrench', color: 'text-sky-600', bg: 'bg-sky-100', border: 'border-sky-200' },
    general: { icon: 'bell', color: 'text-purple-600', bg: 'bg-purple-100', border: 'border-purple-200' },
};

function playNotificationChime() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5 note
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12); // A5 note
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.35);
    } catch (e) {}
}

function triggerBellAnimation() {
    const bellSvg = document.getElementById('bell-icon-svg');
    if (!bellSvg) return;
    bellSvg.classList.add('animate-bounce');
    setTimeout(() => {
        bellSvg.classList.remove('animate-bounce');
    }, 1200);
}

function updateNotificationBadge(unreadCount) {
    const badge = document.getElementById('notification-badge');
    const pill = document.getElementById('dropdown-unread-pill');

    if (badge) {
        if (unreadCount > 0) {
            badge.innerText = unreadCount > 99 ? '99+' : unreadCount;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

    if (pill) {
        if (unreadCount > 0) {
            pill.innerText = `${unreadCount} new`;
            pill.classList.remove('hidden');
        } else {
            pill.classList.add('hidden');
        }
    }
}

function showInteractiveNotificationToast(notif) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none max-w-sm w-full px-4 sm:px-0';
        document.body.appendChild(container);
    }

    const style = NOTIF_ICONS[notif.type] || NOTIF_ICONS.general;
    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-start gap-3 p-3.5 sm:p-4 rounded-2xl border shadow-xl backdrop-blur-md bg-white/95 border-portal-border text-portal-text transition-all duration-300 transform translate-y-0 opacity-100 hover:shadow-2xl';

    toast.innerHTML = `
        <div class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${style.bg} ${style.color} shadow-xs">
            <i data-lucide="${style.icon}" class="w-5 h-5"></i>
        </div>
        <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-1">
                <h4 class="font-bold text-xs text-portal-text leading-tight truncate">${notif.title}</h4>
                <span class="text-[9.5px] font-semibold text-portal-muted shrink-0">${notif.time_ago}</span>
            </div>
            <p class="text-[11px] text-portal-muted mt-1 leading-relaxed line-clamp-2">${notif.message}</p>
            <div class="mt-2.5 flex items-center gap-2">
                <a href="${notif.url}" onclick="handleNotificationClick(${notif.id}, '${notif.url}')" class="inline-flex items-center gap-1 px-3 py-1 bg-portal-primary hover:bg-portal-primary/90 text-white rounded-lg text-[10.5px] font-bold transition-all shadow-xs cursor-pointer">
                    View Details <i data-lucide="arrow-right" class="w-3 h-3"></i>
                </a>
            </div>
        </div>
        <button type="button" class="text-slate-400 hover:text-slate-700 transition-colors p-1 cursor-pointer shrink-0" onclick="this.parentElement.remove()">
            <i data-lucide="x" class="w-3.5 h-3.5"></i>
        </button>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            setTimeout(() => toast.remove(), 300);
        }
    }, 8000);
}

function renderNotificationItemHtml(notif) {
    const style = NOTIF_ICONS[notif.type] || NOTIF_ICONS.general;
    const isUnread = !notif.is_read;
    return `
        <div id="notif-item-${notif.id}" onclick="handleNotificationClick(${notif.id}, '${notif.url}')" class="p-3 px-4 hover:bg-slate-50 transition-colors cursor-pointer flex items-start gap-3 relative ${isUnread ? 'bg-indigo-50/25' : ''}">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${style.bg} ${style.color} shadow-xs mt-0.5">
                <i data-lucide="${style.icon}" class="w-4 h-4"></i>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-1">
                    <h4 class="font-bold text-xs truncate ${isUnread ? 'text-slate-950 font-extrabold' : 'text-slate-700'}">${notif.title}</h4>
                    <span class="text-[9.5px] text-portal-muted shrink-0">${notif.time_ago}</span>
                </div>
                <p class="text-[11px] text-portal-muted mt-0.5 leading-snug line-clamp-2">${notif.message}</p>
            </div>
            ${isUnread ? `<span class="unread-dot w-2 h-2 rounded-full bg-rose-500 shrink-0 mt-2 shadow-xs"></span>` : ''}
        </div>
    `;
}

function prependNotificationToDropdown(notif) {
    const container = document.getElementById('notification-list-container');
    const emptyState = document.getElementById('notifications-empty');
    const loadingState = document.getElementById('notifications-loading');

    if (loadingState) loadingState.classList.add('hidden');
    if (emptyState) emptyState.classList.add('hidden');

    if (container) {
        if (document.getElementById(`notif-item-${notif.id}`)) return;

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = renderNotificationItemHtml(notif);
        const item = tempDiv.firstElementChild;
        if (container.firstElementChild) {
            container.insertBefore(item, container.firstElementChild);
        } else {
            container.appendChild(item);
        }
        if (window.lucide) lucide.createIcons();
    }
}

window.loadNotificationsList = async function() {
    const container = document.getElementById('notification-list-container');
    const emptyState = document.getElementById('notifications-empty');
    const loadingState = document.getElementById('notifications-loading');

    if (!container) return;

    try {
        const res = await fetch('/api/notifications/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        if (data.status !== 'success') return;

        updateNotificationBadge(data.unread_count);

        if (loadingState) loadingState.classList.add('hidden');

        // Remove existing rendered item rows
        container.querySelectorAll('[id^="notif-item-"]').forEach(el => el.remove());

        if (!data.notifications || data.notifications.length === 0) {
            if (emptyState) emptyState.classList.remove('hidden');
        } else {
            if (emptyState) emptyState.classList.add('hidden');
            let html = '';
            data.notifications.forEach(n => {
                html += renderNotificationItemHtml(n);
            });
            container.insertAdjacentHTML('beforeend', html);
            if (window.lucide) lucide.createIcons();
        }
    } catch (e) {
        console.error('[Notifications] Failed to load list:', e);
        if (loadingState) loadingState.classList.add('hidden');
    }
};

window.handleNotificationClick = async function(id, url) {
    await markNotificationRead(id);
    if (url) {
        window.location.href = url;
    }
};

window.markNotificationRead = async function(id) {
    try {
        const res = await fetch(`/api/notifications/${id}/mark-read/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        const data = await res.json();
        if (data.status === 'success') {
            updateNotificationBadge(data.unread_count);
            const item = document.getElementById(`notif-item-${id}`);
            if (item) {
                const dot = item.querySelector('.unread-dot');
                if (dot) dot.remove();
                item.classList.remove('bg-indigo-50/25');
            }
        }
    } catch (e) {
        console.error('[Notifications] Mark read error:', e);
    }
};

window.markAllNotificationsAsRead = async function() {
    try {
        const res = await fetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        const data = await res.json();
        if (data.status === 'success') {
            updateNotificationBadge(0);
            document.querySelectorAll('.unread-dot').forEach(el => el.remove());
            document.querySelectorAll('#notification-list-container [id^="notif-item-"]').forEach(el => {
                el.classList.remove('bg-indigo-50/25');
            });
            showToast('All notifications marked as read', 'info', 2000);
        }
    } catch (e) {
        console.error('[Notifications] Mark all read error:', e);
    }
};

window.togglePushSettingsPanel = function() {
    const panel = document.getElementById('push-settings-panel');
    if (panel) panel.classList.toggle('hidden');
};

async function pollRealtimeNotifications() {
    try {
        const res = await fetch(`/api/notifications/poll/?since_id=${lastSeenNotificationId}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!res.ok) return;
        const data = await res.json();
        if (data.status !== 'success') return;

        updateNotificationBadge(data.unread_count);

        if (isFirstPoll) {
            isFirstPoll = false;
            lastSeenNotificationId = data.latest_id;
            return;
        }

        if (data.new_notifications && data.new_notifications.length > 0) {
            data.new_notifications.forEach(n => {
                showInteractiveNotificationToast(n);
                prependNotificationToDropdown(n);
            });
            playNotificationChime();
            triggerBellAnimation();
            lastSeenNotificationId = Math.max(lastSeenNotificationId, data.latest_id);
        }
    } catch (e) {
        // Network hiccups or offline, fail gracefully
    }
}

window.toggleNotificationModal = function() {
    const modal = document.getElementById('push-notification-dropdown');
    if (modal) {
        const isOpening = modal.classList.contains('hidden');
        modal.classList.toggle('hidden');
        if (isOpening) {
            window.loadNotificationsList();
            updateNotificationUI();
        }
    }
};

// Close dropdown on outside click
document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('push-notification-dropdown');
    const trigger = document.getElementById('push-bell-button');
    if (dropdown && trigger && !trigger.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

// Initialize real-time notification engine
pollRealtimeNotifications();
setInterval(pollRealtimeNotifications, 3500);

document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        pollRealtimeNotifications();
    }
});

window.addEventListener('focus', () => {
    pollRealtimeNotifications();
});
