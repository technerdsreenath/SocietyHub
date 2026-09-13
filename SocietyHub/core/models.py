from django.db import models
from django.contrib.auth.models import User

class PushSubscription(models.Model):
    """
    Stores browser PushSubscription credentials for Web Push Notifications.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"PushSubscription for {self.user.username} ({self.endpoint[:30]}...)"


class Notification(models.Model):
    """
    Stores in-app notifications for users (e.g., maintenance bills, notices, audit reports, complaints).
    """
    TYPE_CHOICES = [
        ('bill', 'Maintenance Bill'),
        ('notice', 'Society Notice'),
        ('report', 'Audit Report'),
        ('complaint', 'Complaint Update'),
        ('general', 'General Alert'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    society = models.ForeignKey('users.Society', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='general', db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    url = models.CharField(max_length=255, default='/dashboard/')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title} -> {self.recipient.username}"

    def time_ago_display(self):
        from django.utils.timezone import now
        from datetime import timedelta
        diff = now() - self.created_at
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() // 60)
            return f"{mins}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            return f"{diff.days}d ago"
        else:
            return self.created_at.strftime("%b %d, %Y")
