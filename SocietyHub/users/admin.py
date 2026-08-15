from django.contrib import admin
from .models import Society, UserProfile

@admin.register(Society)
class SocietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'area','city', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'city','area')
    search_fields = ('name', 'city','area')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'society', 'role', 'contact', 'is_approved', 'wing', 'flat_number', 'flat_name')
    list_filter = ('role', 'is_approved', 'society', 'wing', 'flat_number', 'flat_name')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'contact', 'wing', 'flat_number', 'flat_name')
