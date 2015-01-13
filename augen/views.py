import os.path

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import TemplateView, View

from rest_framework import generics

from augen.models import Tracker
from augen.serializers import TrackerSerializer
from augen.rabbitmq_manager import PikaConnection

import simplejson as json


class TrackerList(generics.ListCreateAPIView):
    queryset = Tracker.objects.all()
    serializer_class = TrackerSerializer


class TrackerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tracker.objects.all()
    serializer_class = TrackerSerializer


class TrackerView(View):
    def __init__(self):
        super(TrackerView, self).__init__()
        self.pc = PikaConnection()
        self.pc.connect()

    def get(self, request, *args, **kwargs):
        # validate 3 mandatory parameters
        params = dict(request.GET)
        if 'deviceID' not in request.GET \
                or 'longitude' not in request.GET \
                or 'latitude' not in request.GET:
            print "FAIL: all"
            return HttpResponse('FAIL')

        # device ID must be a number, though it has a string type
        try:
            int(request.GET['deviceID'])
        except:
            print "deviceID is not number"
            return HttpResponse('FAIL')

        device_id = request.GET['deviceID']
        lat = float(request.GET['latitude'])
        lon = float(request.GET['longitude'])
        alt = float(request.GET['altitude'])
        sat = float(request.GET['satellites'])
        if isinstance(request.GET['speedOTG'], int): 
            speed = float(request.GET['speedOTG'])
        else:
            speed = None
        time = request.GET['time']

        # save to database
        try:
            t = Tracker(device_id=device_id, lon=lon, lat=lat, alt=alt,
                        speed=speed)
            t.save()
        except IntegrityError:
            return HttpResponse('FAIL')

        message = { 'type': 'point', 'lon': lon, 'lat': lat }
        self.pc.publish_message(json.dumps(message))

        return HttpResponse("OK")


class DashboardView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'augen/index.html')
                      #os.path.join(settings.BASE_DIR, '..',
                      #             'bigdrive-angular/app/index.html'))
