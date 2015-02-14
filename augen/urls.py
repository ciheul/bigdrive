from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from augen import views


urlpatterns = [
    url(r'^trackers/push/$', views.TrackerPushView.as_view()),        
    url(r'^trackers/', views.TrackerList.as_view()),        
    url(r'^trackers/(?P<pk>[0-9]+)/$', views.TrackerDetail.as_view()),        
    url(r'^devices/$', views.DeviceList.as_view()),        
    url(r'^devices/(?P<pk>[0-9]+)/$', views.DeviceDetail.as_view()),        
    url(r'', views.DashboardView.as_view()),        
]

urlpatterns = format_suffix_patterns(urlpatterns)
