from django.urls import re_path

from . import views

app_name = "lampi"
urlpatterns = [
    re_path(r'device/(?P<device_id>[0-9a-fA-F]+)', views.DetailView.as_view(), name='detail'),
    re_path(r'', views.IndexView.as_view(), name='index')
]
