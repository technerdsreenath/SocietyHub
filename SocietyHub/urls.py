from django.contrib import admin
from django.urls import path, include
from SocietyHub.users import views
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

    # Add these right here so /superadmin/approvals/ opens directly:
    path('superadmin/approvals/', views.superadmin_approvals_view, name='superadmin_approvals'),
    path('building/<int:pk>/approve/', views.approve_building, name='approve_building'),
    path('building/<int:pk>/reject/', views.reject_building, name='reject_building'),
    path('chairperson/<int:pk>/approve/', views.approve_chairperson, name='approve_chairperson'),
    path('chairperson/<int:pk>/reject/', views.reject_chairperson, name='reject_chairperson'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)