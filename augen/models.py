from django.db import models


class Tracker(models.Model):
    lon = models.FloatField()
    lat = models.FloatField()
    alt = models.FloatField()
    speed = models.FloatField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('date_created',)
