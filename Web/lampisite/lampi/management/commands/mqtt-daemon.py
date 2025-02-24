import re
import json
from paho.mqtt.client import Client
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from lampi.models import *

DEFAULT_USER = 'parked_device_user'

MQTT_BROKER_RE_PATTERN = (r'\$sys\/broker\/connection\/'
                          r'(?P<device_id>[0-9a-f]*)_broker/state')


def device_association_topic(device_id):
    return 'devices/{}/lamp/associated'.format(device_id)


def get_device_id_from_broker_topic(topic):
    results = re.search(MQTT_BROKER_RE_PATTERN, topic.lower())
    return results.group('device_id')


class Command(BaseCommand):
    help = 'Long-running Daemon Process to Integrate MQTT Messages with Django'

    def _create_default_user_if_needed(self):
        # make sure the user account exists that holds all new devices
        try:
            User.objects.get(username=DEFAULT_USER)
        except User.DoesNotExist:
            User.objects.create_user(username=DEFAULT_USER)
            print("Created user {} to own new LAMPI devices"
                  .format(DEFAULT_USER))

    def _on_connect(self, client, userdata, flags, rc):
        self.client.message_callback_add('$SYS/broker/connection/+/state',
                                         self._device_broker_status_change)
        self.client.subscribe('$SYS/broker/connection/+/state')

    def _create_mqtt_client_and_loop_forever(self):
        self.client = Client()
        self.client.on_connect = self._on_connect
        self.client.connect('localhost', port=50001)
        self.client.loop_forever()

    def _device_broker_status_change(self, client, userdata, message):
        print("RECV: '{}' on '{}'".format(message.payload, message.topic))
        # message payload has to treated as type "bytes" in Python 3
        if message.payload == b'1':
            # broker connected
            device_id = get_device_id_from_broker_topic(message.topic)
            try:
                device = Lampi.objects.get(device_id=device_id)
                print("Found {}".format(device))
            except Lampi.DoesNotExist:
                default_user = User.objects.get(username=DEFAULT_USER)
                new_device = Lampi.objects.create(device_id=device_id,
                                                  user=default_user)
                print("Created {}".format(new_device))

    def handle(self, *args, **options):
        self._create_default_user_if_needed()
        self._create_mqtt_client_and_loop_forever()
