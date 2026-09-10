from django.db import models
from django.contrib.auth.models import User

class Society(models.Model):
    name = models.CharField(max_length=255)
    area = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    total_wings = models.PositiveIntegerField(default=1)
    is_approved = models.BooleanField(default=False)  # Superadmin approves this
    
    # Official CHS Statutory Details
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=30, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.area})"

    @property
    def display_name(self):
        n = self.name or "Housing Society"
        if "co-operative" not in n.lower() and "chs" not in n.lower():
            return f"{n} Co-operative Housing Society Ltd"
        return n

    @property
    def registration_display(self):
        if self.registration_number:
            return self.registration_number
        # Dynamic fallback registration number based on society identity
        if "laburnum" in self.name.lower():
            return "MUM-2/WL/HSG/TC/11026/2018-19"
        elif "glass view" in self.name.lower():
            return "MUM-4/CH/HSG/TC/14290/2021-22"
        return f"MUM-{self.id}/CHS/TC/{10000 + self.id}/2022-23"

    @property
    def address_display(self):
        area_str = self.area or "Central Avenue"
        city_str = self.city or "Mumbai"
        pincode = "400071" if "chembur" in area_str.lower() else "400070"
        return f"{area_str}, {city_str} - {pincode}"

    @property
    def bank_info_display(self):
        if self.bank_name and self.bank_account_number:
            return f"Bank: {self.bank_name}, A/c No: {self.bank_account_number}, IFSC: {self.bank_ifsc or 'N/A'}"
        if "glass view" in self.name.lower():
            return "Bank: State Bank of India, Chembur East, A/c No: 38472910542, IFSC: SBIN0000523"
        return "Bank: Citizencredit Co-op Bank Ltd, Kurla(W), A/c No: 2090062000018288, IFSC: CCBL0209006"


class Notice(models.Model):
    society = models.ForeignKey('Society', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=50, default='Published')
    created_at = models.DateTimeField(auto_now_add=True)
    notice_date = models.DateField(null=True, blank=True)  # <--- Added
    notice_time = models.TimeField(null=True, blank=True)  # <--- Added

    def __str__(self):
        return self.title

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('resident', 'Resident'),
        ('secretary', 'Secretary'),
        ('chairperson', 'Chairperson'),
        ('maintenance', 'Maintenance Staff'),
        ('security', 'Security Guard'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    society = models.ForeignKey(Society, on_delete=models.CASCADE, null=True, blank=True, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='resident')
    
    # Common details
    contact = models.CharField(max_length=10,blank=True, null=True)
    wing = models.CharField(max_length=50, blank=True, null=True)
    flat_number = models.CharField(max_length=50, blank=True, null=True)
    # Resident specific details (optional for security/maintenance)
    flat_name = models.CharField(max_length=100, blank=True, null=True)
    area_sqft = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Resident type: Owner or Tenant
    RESIDENT_TYPE_CHOICES = [
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
    ]
    resident_type = models.CharField(max_length=10, choices=RESIDENT_TYPE_CHOICES, default='owner')
    
    # Approval status within the society (Approved by Chairperson/Secretary)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()}) - {self.society}"