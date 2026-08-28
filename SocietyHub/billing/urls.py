from django.urls import path
from . import views

urlpatterns = [
    path('', views.billing_home, name='billing_home'),
    path('history/', views.billing_home, name='payment_history'),
    path('pay/', views.initiate_payment_view, name='initiate_payment'),
    path('pay/<int:pk>/', views.pay_bill_view, name='pay_bill'),
    path('maintenance/set/', views.set_maintenance_view, name='set_maintenance'),
    path('callback/', views.payment_callback_view, name='payment_callback'),
    path('bill/<int:pk>/', views.view_bill_view, name='view_bill'),
    path('bill/<int:pk>/pdf/', views.download_bill_pdf_view, name='download_bill_pdf'),
    path('bill/<int:pk>/delete/', views.delete_bill_view, name='delete_bill'),
    path('bills/bulk-delete/', views.delete_bulk_bills_view, name='delete_bulk_bills'),
    path('receipt/<int:pk>/', views.view_receipt_view, name='view_receipt'),
    path('receipt/<int:pk>/pdf/', views.download_receipt_pdf_view, name='download_receipt_pdf'),
]
