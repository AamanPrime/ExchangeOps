from django.db import models
from django.contrib.auth.models import User

class Exchange(models.Model):
    name = models.CharField(max_length=50, unique=True)
    simulator_base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ConnectionEvent(models.Model):
    STATUS_CHOICES = [
        ('UP', 'UP'),
        ('DOWN', 'DOWN'),
        ('DEGRADED', 'DEGRADED'),
    ]
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    consecutive_misses = models.IntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exchange.name} - {self.status} at {self.recorded_at}"

class Incident(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'LOW'),
        ('MEDIUM', 'MEDIUM'),
        ('HIGH', 'HIGH'),
    ]
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='incidents')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    opened_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    auto_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        status = "RESOLVED" if self.resolved_at else "OPEN"
        return f"Incident {self.id}: {self.exchange.name} ({status})"
