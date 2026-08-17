from django.urls import path
from . import views

urlpatterns = [
    path('', views.complaints_list_view, name='complaints_list'),
    path('create/', views.create_complaint_view, name='create_complaint'),
    path('<int:pk>/accept/', views.accept_complaint_view, name='accept_complaint'),
    path('<int:pk>/complete/', views.complete_complaint_view, name='complete_complaint'),
    path('<int:pk>/close/', views.close_complaint_view, name='close_complaint'),
    path('<int:pk>/feedback/<str:feedback>/', views.approve_complaint_resolution, name='approve_complaint_resolution'),
]
