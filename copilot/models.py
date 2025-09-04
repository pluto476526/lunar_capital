## copilot/models.py
## pkibuka@milky-way.space


from django.db import models

class MarketData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Bullish')
    volatility = models.FloatField(default=18.5)
    active_alerts = models.IntegerField(default=14)
    session_activity = models.CharField(max_length=20, default='High')
    trending_up = models.IntegerField(default=72)
    volatility_change = models.IntegerField(default=12)
    alerts_change = models.IntegerField(default=3)
    current_session = models.CharField(max_length=20, default='London')

    class Meta:
        ordering = ['-timestamp']
