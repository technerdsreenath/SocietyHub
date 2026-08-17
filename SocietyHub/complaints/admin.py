from django.contrib import admin
from .models import Complaint

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'society', 'category', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'category', 'society')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
