from django.urls import path
from . import views

urlpatterns = [
    path('', views.amenity_list_view, name='amenity_list'),
    path('book/<int:amenity_id>/', views.book_amenity_view, name='book_amenity'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('cancel/<int:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('society-bookings/', views.society_bookings_view, name='society_bookings'),
    path('edit-price/<int:amenity_id>/', views.edit_amenity_price_view, name='edit_amenity_price'),
    path('add/', views.add_amenity_view, name='add_amenity'),
]
