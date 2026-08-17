from django.db import models
from django.contrib.auth.models import User
from SocietyHub.users.models import Society

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Closed', 'Closed'),
        ('Approved', 'Approved'),
    ]

    CATEGORY_CHOICES = [
        ('Electrical', 'Electrical'),
        ('Plumbing', 'Plumbing'),
        ('Security', 'Security'),
        ('Maintenance', 'Maintenance'),
        ('General', 'General'),
    ]

    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='complaints')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='filed_complaints')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status}) - {self.society}"

    @property
    def date(self):
        return self.created_at.strftime('%b %d, %Y')

    @property
    def status_class(self):
        if self.status == 'Pending':
            return 'text-amber-700 bg-amber-50 border border-amber-200'
        elif self.status == 'In Progress':
            return 'text-blue-700 bg-blue-50 border border-blue-200'
        elif self.status == 'Completed':
            return 'text-green-700 bg-green-50 border border-green-200'
        elif self.status == 'Approved':
            return 'text-emerald-700 bg-emerald-50 border border-emerald-200'
        else: # Closed
            return 'text-gray-700 bg-gray-50 border border-gray-200'
