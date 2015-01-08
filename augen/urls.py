from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from augen import views


urlpatterns = [
    url(r'^trackers/push/$', views.TrackerView.as_view()),        
    url(r'^trackers/$', views.TrackerList.as_view()),        
    url(r'^trackers/(?P<pk>[0-9]+)/$', views.TrackerDetail.as_view()),        
    url(r'', views.DashboardView.as_view()),        
]

urlpatterns = format_suffix_patterns(urlpatterns)
