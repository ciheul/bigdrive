from datetime import datetime
import os.path

import simplejson as json

from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import TemplateView, View

from augen.models import Device, Tracker
from augen import serializers
from augen.rabbitmq_manager import PikaConnection

from rest_framework import generics


TRUE = 1
FALSE = 0


class TrackerList(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if int(self.request.QUERY_PARAMS.get('aggregate', FALSE)) == TRUE:
            return serializers.TrackerAggregateSerializer
        return serializers.TrackerSerializer

    def get_queryset(self):
        query = Q()

        # TODO any wrong parameters, raise Http404
        device_name = self.request.QUERY_PARAMS.get('deviceID', None)
        if device_name is not None:
            #return Tracker.objects.all()
            query &= Q(device__name=device_name)
        
        # add date_selected if it exists
        date_selected = self.request.QUERY_PARAMS.get('dateSelected', None)
        if date_selected is not None:
            try:
                d = datetime.strptime(date_selected, '%Y-%m-%d').date()
            except ValueError:
                raise Http404
            query &= Q(date_created__year=d.year,
                       date_created__month=d.month,
                       date_created__day=d.day)

        ts = Tracker.objects.filter(query).order_by('-date_created')

        if int(self.request.QUERY_PARAMS.get('aggregate', FALSE)) == TRUE:
            return self.aggregate_points(ts)

        return ts

    def aggregate_points(self, ts):
        aggr = list()
        prev = ts[0]
        total = 1
        for i, t in enumerate(ts):
            if i == 0: continue

            # compare with previous element in list
            if ts[i].lat != prev.lat and ts[i] != prev.lon \
                    and ts[i] != prev.alt:
                # if different, append to aggr list
                point = { 'lon': prev.lon, 'lat': prev.lat, 'alt': prev.alt,
                          'total': total }
                aggr.append(point)

                # start new comparation point
                prev = ts[i]
                total = 1
            else:
                total += 1
        point = { 'lon': prev.lon, 'lat': prev.lat, 'alt': prev.alt,
                  'total': total }
        aggr.append(point)

        return aggr


class TrackerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tracker.objects.all()
    serializer_class = serializers.TrackerSerializer


class TrackerPushView(View):
    def __init__(self):
        super(TrackerPushView, self).__init__()
        self.pc = PikaConnection()
        self.pc.connect()

    def get(self, request, *args, **kwargs):
        """Push track history using GET method. A little bit awkward."""

        # validate 3 mandatory parameters
        params = dict(request.GET)
        if 'deviceID' not in request.GET \
                or 'longitude' not in request.GET \
                or 'latitude' not in request.GET:
            print "FAIL: all"
            return HttpResponse('FAIL')

        # device ID must be a number, though it has a string type
        #try:
        #    int(request.GET['deviceID'])
        #except:
        #    print "deviceID is not number"
        #    return HttpResponse('FAIL')

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
            print "FAIL: saving to database"
            return HttpResponse('FAIL')

        message = { 'type': 'point', 'lon': lon, 'lat': lat }
        self.pc.publish_message(json.dumps(message))

        return HttpResponse("OK")


class DeviceList(generics.ListCreateAPIView):
    queryset = Device.objects.all()
    serializer_class = serializers.DeviceSerializer


class DeviceDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Device.objects.all()
    serializer_class = serializers.DeviceSerializer


class DashboardView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'augen/index.html')
                      #os.path.join(settings.BASE_DIR, '..',
                      #             'bigdrive-angular/app/index.html'))
