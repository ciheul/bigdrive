from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import TemplateView, View

from rest_framework import generics

from augen.models import Tracker
from augen.serializers import TrackerSerializer


class TrackerList(generics.ListCreateAPIView):
    queryset = Tracker.objects.all()
    serializer_class = TrackerSerializer


class TrackerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tracker.objects.all()
    serializer_class = TrackerSerializer


class TrackerView(View):
    def get(self, request, *args, **kwargs):
        lat = float(request.GET['latitude'])
        lon = float(request.GET['longitude'])
        alt = float(request.GET['altitude'])
        sat = float(request.GET['satellites'])
        if isinstance(request.GET['speedOTG'], int): 
            speed = float(request.GET['speedOTG'])
        else:
            speed = None
        time = request.GET['time']

        t = Tracker(lon=lon, lat=lat, alt=alt, speed=speed)
        t.save()

        return HttpResponse("OK")


class DashboardView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'augen/index.html')
