from django.urls import path
from . import views

urlpatterns = [
    path('check-in/', views.check_in_visitor, name='check_in_visitor'),
    path('checkout/<int:pk>/', views.check_out_visitor, name='check_out_visitor'),
    path('log/', views.visitor_log_view, name='visitor_log'),
]
