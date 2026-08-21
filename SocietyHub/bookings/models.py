from django.db import models
from django.contrib.auth.models import User

class Amenity(models.Model):
    society = models.ForeignKey('users.Society', on_delete=models.CASCADE, related_name='amenities', null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    booking_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.society.name if self.society else 'Global'}"

class AmenityBooking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amenity_bookings')
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amenity.name} on {self.booking_date}"

    @property
    def date_display(self):
        return self.booking_date.strftime('%b %d, %Y')

    @property
    def time_range_display(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

    @property
    def facility(self):
        return self.amenity.name

    @property
    def date(self):
        return self.date_display

    @property
    def time(self):
        return self.time_range_display

    @property
    def status_class(self):
        if self.status == 'Confirmed':
            return 'text-emerald-700 bg-emerald-50 border border-emerald-200'
        elif self.status == 'Pending':
            return 'text-amber-700 bg-amber-50 border border-amber-200'
        else: # Cancelled
            return 'text-red-700 bg-red-50 border border-red-200'
