from django.shortcuts import render
from .models import SystemData

def latest_message(request):
    message = SystemData.objects.latest('timestamp')
    return render(request, 'aggregator/latest_message.html', {'message': message})
