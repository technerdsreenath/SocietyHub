from django.contrib import admin
from .models import PaymentTransaction, MaintenanceScheduleConfig

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'user', 'society', 'payment_type', 'amount', 'status', 'created_at')
    list_filter = ('status', 'payment_type', 'society', 'created_at')
    search_fields = ('receipt_number', 'user__username', 'user__first_name', 'user__last_name', 'razorpay_payment_id', 'razorpay_order_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MaintenanceScheduleConfig)
class MaintenanceScheduleConfigAdmin(admin.ModelAdmin):
    list_display = ('society', 'is_auto_dispatch_active', 'dispatch_day', 'frequency', 'due_days', 'last_dispatched_period', 'last_dispatched_date')
    list_filter = ('is_auto_dispatch_active', 'frequency')
    search_fields = ('society__name',)

