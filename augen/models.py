from django.db import models


class Tracker(models.Model):
    device_id = models.CharField(max_length=30)
    lon = models.FloatField()
    lat = models.FloatField()
    alt = models.FloatField(null=True)
    speed = models.FloatField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)
