from django.db import models
from django.contrib.auth.models import User

class Society(models.Model):
    name = models.CharField(max_length=255)
    area = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    total_wings = models.PositiveIntegerField(default=1)
    is_approved = models.BooleanField(default=False)  # Superadmin approves this
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.area})"

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