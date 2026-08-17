from django.contrib import admin
from .models import Visitor

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'society', 'apartment', 'purpose', 'entry_time', 'exit_time', 'status')
    list_filter = ('status', 'purpose', 'society')
    search_fields = ('name', 'contact', 'apartment')
