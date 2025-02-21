from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'device/(?P<device_id>[0-9a-fA-F]+)', views.DetailView.as_view(), name='detail'),
]
