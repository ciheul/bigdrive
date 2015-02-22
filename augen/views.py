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

        if int(self.request.QUERY_PARAMS.get('aggregate', FALSE)) == TRUE \
                and len(ts) > 0:
            return self.aggregate_points(ts)

        return ts

    def aggregate_points(self, ts):
        aggr = list()

        # find first valid coordinate
        for i, t in enumerate(ts):
            # remove coordinate
            if ts[i].lat == 0 and ts[i].lat == 0: continue

            #if ts[i].lat < -90 or ts[i].lat > 90 \
            #        or ts[i].lon < -180 or ts[i].lon > 180:
            #    continue

            ts[i].lon = self.convert_nmea_to_dd(ts[i].lon)
            ts[i].lat = self.convert_nmea_to_dd(ts[i].lat)

            #print "pre lat: %f, lon: %f" % (ts[i].lat, ts[i].lon)
            #print -1.0 < ts[i].lat < 1.0, -5.0 < ts[i].lon < 5.0
            if (-1 < ts[i].lat < 1) and (-5 < ts[i].lon < 5):
                continue
            prev = ts[i]
            start = i
            break
        #print "prev:", prev.lat, prev.lon
        #print "start:", start
        #print


        #prev = ts[0]
        #print prev.lat, prev.lon
        total = 1
        for i, t in enumerate(ts):
            if i in range(start): continue
            if ts[i].lat == 0 and ts[i].lat == 0: continue

            #pdb.set_trace()
            # invalid lon lat
            #if ts[i].lat < -90 or ts[i].lat > 90 \
            #        or ts[i].lon < -180 or ts[i].lon > 180:
            #    continue
            #print "lat: %f, lon: %f" % (ts[i].lat, ts[i].lon)

            deg_lon = self.convert_nmea_to_dd(ts[i].lon)
            deg_lat = self.convert_nmea_to_dd(ts[i].lat)

            #print "lat: %f, lon: %f" % (deg_lat, deg_lon)
            #print -1.0 < ts[i].lat < 1.0, -5.0 < ts[i].lon < 5.0
            if (-1 < deg_lat < 1) and (-5 < deg_lon < 5):
                #print "remove"
                #print
                continue

            #print "prev:", prev.lat, prev.lon
            # compare with previous element in list
            if deg_lat != prev.lat and deg_lon != prev.lon \
                    and ts[i].alt != prev.alt:
                # if different, append to aggr list
                point = { 'lon': prev.lon, 'lat': prev.lat, 'alt': prev.alt,
                          'total': total }
                #print point
                #print
                aggr.append(point)

                # start new comparation point
                ts[i].lat = deg_lat
                ts[i].lon = deg_lon
                prev = ts[i]
                total = 1
            else:
                total += 1
        point = { 'lon': prev.lon, 'lat': prev.lat, 'alt': prev.alt,
                  'total': total }
        aggr.append(point)

        return aggr

    def convert_nmea_to_dd(self, value):
        """Convert a NMEA decimal-decimal degree value into decimal degrees.
           Example: value = 5144.3855 (ddmm.mmmm)
                          = 51 44.3855
                          = 51 + 44.3855/60
                          = 51.7397583 degrees
        """
        negative = False
        if value < 0:
            negative = True

        deg_value = abs(value) / 100
        degrees = int(deg_value)

        result = degrees + ((deg_value - degrees) / .60)
        if negative == True:
            result *= -1
        return result

    # https://community.oracle.com/thread/3619431
    def convert_dd_to_degrees(self, dec_ms):
        minute_value = dec_ms * 60
        minutes = int(minute_value)
        sec_value = (minute_value - minutes) * 60


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
            print "FAIL: mandatory parameters are incorrect"
            return HttpResponse('FAIL: mandatory parameters are incorrect')

        try:
            device = Device.objects.get(name=request.GET['deviceID'])
        except Device.DoesNotExist:
            print "FAIL: device is not registered"
            return HttpResponse('FAIL: device %s is not registered' %
                                request.GET['deviceID'])

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
            t = Tracker(device=device, lon=lon, lat=lat, alt=alt,
                        speed=speed)
            t.save()
        except IntegrityError:
            print "FAIL: saving to database"
            return HttpResponse('FAIL: saving to database')

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
