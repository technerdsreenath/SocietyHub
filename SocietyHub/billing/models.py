import datetime
import random
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from SocietyHub.users.models import Society

class PaymentTransaction(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('maintenance', 'Maintenance Bill'),
        ('repair_fund', 'Maintenance Bill'),
        ('service_charges', 'Service & Maintenance Charges'),
        ('sinking_fund', 'Sinking Fund'),
        ('water_charges', 'Water Charges'),
        ('parking_charges', 'Parking Charges'),
        ('property_tax', 'Property Taxes & Dues'),
        ('non_occupancy', 'Non-Occupancy Charges'),
        ('penalty', 'Late Payment Penalty'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default='service_charges')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Auto-generated unique receipt number upon successful payment (e.g., SH-REC-2026-0001)
    receipt_number = models.CharField(max_length=60, unique=True, null=True, blank=True)
    
    # Standard Razorpay integration fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)
    
    # Itemized CHS Maintenance Bill fields
    bill_number = models.CharField(max_length=50, null=True, blank=True)
    bill_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    billing_period = models.CharField(max_length=100, null=True, blank=True)
    breakdown_json = models.TextField(null=True, blank=True) # Stores itemized particulars list as JSON
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrears_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_payment_type_display()} - ₹{self.amount} ({self.status}) - {self.user.username}"

    def get_breakdown(self):
        import json
        if self.breakdown_json:
            try:
                return json.loads(self.breakdown_json)
            except Exception:
                pass
        return [
            {"particular": self.get_payment_type_display(), "amount": float(self.amount)}
        ]

    @classmethod
    def generate_bill_number(cls):
        last_bill = cls.objects.exclude(bill_number__isnull=True).exclude(bill_number='').order_by('-id').first()
        if last_bill and last_bill.bill_number:
            try:
                num = int(''.join(filter(str.isdigit, str(last_bill.bill_number))))
                return str(num + 1)
            except Exception:
                return str(random.randint(10, 999))
        return "29"

    @classmethod
    def generate_receipt_number(cls):
        year = datetime.date.today().year
        prefix = f"SH-REC-{year}"
        existing = cls.objects.filter(receipt_number__startswith=prefix).values_list('receipt_number', flat=True)
        max_seq = 0
        for r_num in existing:
            if r_num:
                try:
                    seq_part = int(r_num.split('-')[-1])
                    if seq_part > max_seq:
                        max_seq = seq_part
                except (ValueError, IndexError):
                    pass

        new_seq = max_seq + 1
        candidate = f"{prefix}-{new_seq:04d}"
        while cls.objects.filter(receipt_number=candidate).exists():
            new_seq += 1
            candidate = f"{prefix}-{new_seq:04d}"
        return candidate


class MaintenanceScheduleConfig(models.Model):
    """
    Automated Maintenance Billing Schedule configuration for each society.
    Allows the system to automatically generate and dispatch itemized bills
    to all approved residents on the designated recurring calendar date.
    """
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly (Every Month)'),
        ('quarterly', 'Quarterly (Every 3 Months)'),
    ]

    society = models.OneToOneField(Society, on_delete=models.CASCADE, related_name='maintenance_schedule')
    is_auto_dispatch_active = models.BooleanField(
        default=True, 
        help_text="When enabled, bills are automatically generated and dispatched on the scheduled date"
    )
    dispatch_day = models.PositiveSmallIntegerField(
        default=1, 
        help_text="Day of the month to dispatch bills automatically (1 to 28)"
    )
    frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES, 
        default='monthly'
    )
    due_days = models.PositiveSmallIntegerField(
        default=15, 
        help_text="Days from bill dispatch until due date (e.g., 15 days)"
    )

    # Saved Statutory Head Rates (Defaulted to Maharashtra CHS Model Bye-Law #67 standards)
    prop_tax_rate = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal('5.026'))
    prop_tax_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    sinking_rate = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal('1.569'))
    sinking_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    repair_rate = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal('3.147'))
    repair_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    service_rate = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal('0.00'))
    service_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('3600.00'))

    electricity_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1350.00'))
    water_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('450.00'))
    security_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('2100.00'))
    parking_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    non_occupancy_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    last_dispatched_date = models.DateField(null=True, blank=True)
    last_dispatched_period = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule for {self.society.name} (Day {self.dispatch_day}, {self.frequency})"

    def get_current_period_label(self, ref_date=None):
        import datetime
        d = ref_date or datetime.date.today()
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        if self.frequency == 'monthly':
            return f"{month_names[d.month]} {d.year}"
        elif self.frequency == 'quarterly':
            q_idx = (d.month - 1) // 3
            quarters = [
                f"Q1 (Jan/Feb/Mar) {d.year}",
                f"Q2 (Apr/May/Jun) {d.year}",
                f"Q3 (Jul/Aug/Sep) {d.year}",
                f"Q4 (Oct/Nov/Dec) {d.year}"
            ]
            return quarters[q_idx]
        return f"{month_names[d.month]} {d.year}"

    def get_next_dispatch_date(self, ref_date=None):
        import datetime
        today = ref_date or datetime.date.today()
        day = min(max(self.dispatch_day, 1), 28)
        try:
            target_this_month = datetime.date(today.year, today.month, day)
        except ValueError:
            target_this_month = datetime.date(today.year, today.month, 28)

        if target_this_month > today:
            return target_this_month
        
        # Next cycle
        if self.frequency == 'quarterly':
            current_q = (today.month - 1) // 3
            next_q_month = ((current_q + 1) * 3) + 1
            next_year = today.year
            if next_q_month > 12:
                next_q_month = 1
                next_year += 1
            return datetime.date(next_year, next_q_month, day)
        else:
            next_month = today.month + 1
            next_year = today.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            return datetime.date(next_year, next_month, day)


class AuditReport(models.Model):
    """
    Official Society Financial & Statutory Audit Reports uploaded by the Chairperson.
    Downloadable and verifiable by all approved residents and committee members of the society.
    """
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='audit_reports')
    title = models.CharField(max_length=255)
    financial_year = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. FY 2025-26")
    auditor_name = models.CharField(max_length=255, blank=True, null=True, help_text="Chartered Accountant or Audit Firm Name")
    audit_date = models.DateField(null=True, blank=True, help_text="Date audit completed or submitted")
    file = models.FileField(upload_to='audit_reports/')
    file_size_display = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True, help_text="Key auditor observations, opinions, or summary")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_audits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-audit_date', '-created_at']

    def __str__(self):
        year_str = f" ({self.financial_year})" if self.financial_year else ""
        return f"{self.title}{year_str} - {self.society.name}"

    def get_extension(self):
        if self.file and '.' in self.file.name:
            return self.file.name.rsplit('.', 1)[-1].upper()
        return "PDF"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size_display:
            try:
                size_bytes = self.file.size
                if size_bytes < 1024:
                    self.file_size_display = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    self.file_size_display = f"{size_bytes / 1024:.1f} KB"
                else:
                    self.file_size_display = f"{size_bytes / (1024 * 1024):.1f} MB"
            except Exception:
                pass
        super().save(*args, **kwargs)

