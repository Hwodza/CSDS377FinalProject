from django.shortcuts import render
from .models import SystemData


def latest_message(request):
    try:
        message = SystemData.objects.latest('timestamp')
        context = {'message': message}
    except SystemData.DoesNotExist:
        context = {'message': None}
    return render(request, 'aggregator/latest_message.html', context)
