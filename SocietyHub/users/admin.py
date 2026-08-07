from django.contrib import admin
from .models import Society, UserProfile

@admin.register(Society)
class SocietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'city')
    search_fields = ('name', 'city')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'society', 'role', 'contact', 'is_society_approved')
    list_filter = ('role', 'is_society_approved', 'society')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'contact')
