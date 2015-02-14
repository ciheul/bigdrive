from django.db import models


# User model should be created along Authentication


class Device(models.Model):
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name


class Tracker(models.Model):
    device = models.ForeignKey(Device)
    lon = models.FloatField()
    lat = models.FloatField()
    alt = models.FloatField(null=True)
    speed = models.FloatField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)
