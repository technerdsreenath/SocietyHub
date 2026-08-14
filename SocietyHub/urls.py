from django.contrib import admin
from django.urls import path, include
from SocietyHub.users import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('SocietyHub.users.urls')),
    path('', include('SocietyHub.core.urls')),

    # Add these right here so /superadmin/approvals/ opens directly:
    path('superadmin/approvals/', views.superadmin_approvals_view, name='superadmin_approvals'),
    path('building/<int:pk>/approve/', views.approve_building, name='approve_building'),
    path('building/<int:pk>/reject/', views.reject_building, name='reject_building'),
    path('chairperson/<int:pk>/approve/', views.approve_chairperson, name='approve_chairperson'),
    path('chairperson/<int:pk>/reject/', views.reject_chairperson, name='reject_chairperson'),
]