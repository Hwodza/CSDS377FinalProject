from django.urls import path
from . import views

urlpatterns = [
    path('', views.latest_message, name='latest_message'),
]
