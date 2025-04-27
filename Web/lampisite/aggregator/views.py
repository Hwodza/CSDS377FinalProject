from django.shortcuts import render
from .models import SystemData
from django.http import JsonResponse


def latest_message(request):
    try:
        message = SystemData.objects.latest('timestamp')
        context = {'message': message}
    except SystemData.DoesNotExist:
        context = {'message': None}
    return render(request, 'aggregator/latest_message.html', context)


def latest_message_json(request):
    try:
        message = SystemData.objects.latest('timestamp')
        data = {
            'topic': message.topic,
            'payload': message.payload,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }
    except SystemData.DoesNotExist:
        data = {'error': 'No messages received yet.'}
    return JsonResponse(data)
