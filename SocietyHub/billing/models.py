import datetime
import random
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
