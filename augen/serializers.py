from rest_framework import serializers
from augen.models import Tracker


class TrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracker
        fields = ('device_id', 'lon', 'lat', 'alt', 'speed', 'date_created')
