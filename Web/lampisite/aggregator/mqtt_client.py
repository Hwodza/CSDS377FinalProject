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
    mqtt.publish.singe("devices/b827ebdb1727/sender/hello", msg.payload, qos=1,
                       retain=False, hostname="localhost", port=50001)


def start_mqtt():
    def run():
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect("localhost", port=50001)
        client.loop_forever()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
