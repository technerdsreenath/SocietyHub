from django.contrib import admin
from .models import Amenity, AmenityBooking

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'society', 'booking_fee', 'open_time', 'close_time', 'is_active')
    list_filter = ('is_active', 'society')
    search_fields = ('name', 'description')

@admin.register(AmenityBooking)
class AmenityBookingAdmin(admin.ModelAdmin):
    list_display = ('amenity', 'user', 'booking_date', 'start_time', 'end_time', 'status', 'created_at')
    list_filter = ('status', 'booking_date', 'amenity__society')
    search_fields = ('user__username', 'amenity__name')
