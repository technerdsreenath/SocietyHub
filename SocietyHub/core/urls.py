from django.urls import path
from django.views.generic import RedirectView
from .views import portal_dashboard

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    path('dashboard/', portal_dashboard, name='portal_dashboard'),
]
