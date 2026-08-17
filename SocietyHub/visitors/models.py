from django.db import models
from SocietyHub.users.models import Society

class Visitor(models.Model):
    STATUS_CHOICES = [
        ('Checked In', 'Checked In'),
        ('Checked Out', 'Checked Out'),
    ]
    
    PURPOSE_CHOICES = [
        ('Delivery (Amazon/Zomato)', 'Delivery (Amazon/Zomato)'),
        ('Personal Guest', 'Personal Guest'),
        ('Maintenance / Service', 'Maintenance / Service'),
        ('Courier / Post', 'Courier / Post'),
    ]

    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='visitors')
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=20)
    apartment = models.CharField(max_length=50)
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Checked In')

    def __str__(self):
        return f"{self.name} - {self.apartment} ({self.status})"

    @property
    def badge_color(self):
        return 'bg-emerald-500' if self.status == 'Checked In' else 'bg-gray-400'
