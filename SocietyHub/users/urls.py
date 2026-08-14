from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    register_view, logout_view, admin_approvals_view, approve_user_view,
    CustomLoginView, superadmin_approvals_view, approve_building, reject_building,
    approve_chairperson, reject_chairperson, chairperson_approvals_view,
    approve_secretary, reject_secretary, secretary_approvals_view,
    approve_resident, reject_resident
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Password Reset Routes
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
    
    # Staff / Admin Approval Routes
    path('approvals/', admin_approvals_view, name='admin_approvals'),
    path('approvals/approve/<int:profile_id>/', approve_user_view, name='approve_user'),
    
    # Superadmin Approvals
    path('superadmin/approvals/', views.superadmin_approvals_view, name='superadmin_approvals'),
    path('building/<int:pk>/approve/', views.approve_building, name='approve_building'),
    path('building/<int:pk>/reject/', views.reject_building, name='reject_building'),
    path('chairperson/<int:pk>/approve/', views.approve_chairperson, name='approve_chairperson'),
    path('chairperson/<int:pk>/reject/', views.reject_chairperson, name='reject_chairperson'),

    # Chairperson Approvals (Approve Secretary)
    path('chairperson/approvals/', views.chairperson_approvals_view, name='chairperson_approvals'),
    path('secretary/<int:pk>/approve/', views.approve_secretary, name='approve_secretary'),
    path('secretary/<int:pk>/reject/', views.reject_secretary, name='reject_secretary'),

    # Secretary Approvals (Approve Resident)
    path('secretary/approvals/', views.secretary_approvals_view, name='secretary_approvals'),
    path('resident/<int:pk>/approve/', views.approve_resident, name='approve_resident'),
    path('resident/<int:pk>/reject/', views.reject_resident, name='reject_resident'),
]



