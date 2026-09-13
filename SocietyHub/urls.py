from django.contrib import admin
from django.urls import path, include
from SocietyHub.users import views
from SocietyHub.core import views as core_views
from django.contrib.auth import views as auth_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('SocietyHub.users.urls')),
    path('visitors/', include('SocietyHub.visitors.urls')),
    path('complaints/', include('SocietyHub.complaints.urls')),
    path('bookings/', include('SocietyHub.bookings.urls')),
    path('billing/', include('SocietyHub.billing.urls')),
    path('', include('SocietyHub.core.urls')),

    # PWA & Service Worker endpoints (Served at root for scope '/')
    path('manifest.json', core_views.manifest_view, name='pwa_manifest'),
    path('sw.js', core_views.service_worker_view, name='pwa_sw'),
    path('offline/', core_views.offline_view, name='pwa_offline'),

    # Web Push Notification APIs
    path('api/push/vapid-key/', core_views.get_vapid_public_key_api, name='push_vapid_key'),
    path('api/push/subscribe/', core_views.push_subscribe_api, name='push_subscribe'),
    path('api/push/unsubscribe/', core_views.push_unsubscribe_api, name='push_unsubscribe'),
    path('api/push/test/', core_views.push_test_api, name='push_test'),

    # Real-Time In-App Notification APIs
    path('api/notifications/poll/', core_views.notifications_poll_api, name='notifications_poll_api'),
    path('api/notifications/', core_views.notifications_list_api, name='notifications_list_api'),
    path('api/notifications/<int:pk>/mark-read/', core_views.notification_mark_read_api, name='notification_mark_read_api'),
    path('api/notifications/mark-all-read/', core_views.notifications_mark_all_read_api, name='notifications_mark_all_read_api'),

    # Add these right here so /superadmin/approvals/ opens directly:
    path('superadmin/approvals/', views.superadmin_approvals_view, name='superadmin_approvals'),
    path('building/<int:pk>/approve/', views.approve_building, name='approve_building'),
    path('building/<int:pk>/reject/', views.reject_building, name='reject_building'),
    path('chairperson/<int:pk>/approve/', views.approve_chairperson, name='approve_chairperson'),
    path('chairperson/<int:pk>/reject/', views.reject_chairperson, name='reject_chairperson'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)