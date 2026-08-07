from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('SocietyHub.users.urls')),
    path('', include('SocietyHub.core.urls')),
]