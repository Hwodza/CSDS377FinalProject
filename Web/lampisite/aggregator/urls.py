from django.urls import path
from . import views

app_name = 'aggregator'

urlpatterns = [
    path('', views.latest_message, name='latest_message'),
    path('latest-message/json/', views.latest_message_json,
         name='latest_message_json'),
]
