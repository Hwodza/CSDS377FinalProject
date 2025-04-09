import threading
import paho.mqtt.client as mqtt
from .models import SystemData
import django
import os
import time


# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project_name.settings")
# django.setup()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("senders/#")


def on_message(client, userdata, msg):
    print(f"Received message: {msg.topic} -> {msg.payload.decode()}")
    SystemData.objects.create(
        topic=msg.topic,
        payload=msg.payload.decode()
    )


def start_mqtt():
    def run():
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect("localhost", 50001, 60)
        client.loop_forever()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
