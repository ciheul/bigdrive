from rest_framework import serializers
from augen.models import Device, Tracker


class TrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracker
        fields = ('device', 'lon', 'lat', 'alt', 'speed', 'date_created',)


class TrackerAggregateSerializer(serializers.Serializer):
    lon = serializers.FloatField()
    lat = serializers.FloatField()
    alt = serializers.FloatField()
    total = serializers.IntegerField()


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('name',)
