from django.db import models
from django.conf import settings

class SimulationSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='simulation_sessions')
    name = models.CharField(max_length=255, default='Unnamed Session')
    scenario = models.CharField(max_length=255)
    current_tick = models.IntegerField(default=0)
    nav = models.FloatField(default=10000.0)
    cash = models.FloatField(default=10000.0)
    state_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.created_at.date()})"
