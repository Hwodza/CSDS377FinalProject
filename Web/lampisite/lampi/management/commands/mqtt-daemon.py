import re
import json
from datetime import datetime
from django.utils import timezone
from paho.mqtt.client import Client
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.conf import settings
from lampi.models import *
from mixpanel import Mixpanel


MQTT_BROKER_RE_PATTERN = (r'\$sys\/broker\/connection\/'
                          r'(?P<device_id>[0-9a-f]*)_broker/state')
MQTT_SENDER_BROKER_RE_PATTERN = (r'\$sys\/broker\/connection\/'
                                 r'(?P<device_id>[0-9a-f]*)_sender_broker/'
                                 r'state')
MQTT_SENDER_STATS_RE_PATTERN = r'senders\/(?P<device_id>[0-9a-f]*)\/stats\/'
DEVICE_STATE_RE_PATTERN = r'devices\/(?P<device_id>[0-9a-f]*)\/lamp\/changed'


def device_association_topic(device_id):
    return 'devices/{}/lamp/associated'.format(device_id)


class Command(BaseCommand):
    help = 'Long-running Daemon Process to Integrate MQTT Messages with Django'

    def _create_default_user_if_needed(self):
        # make sure the user account exists that holds all new devices
        try:
            User.objects.get(username=settings.DEFAULT_USER)
        except User.DoesNotExist:
            print("Creating user {} to own new LAMPI devices".format(
                settings.DEFAULT_USER))
            new_user = User()
            new_user.username = settings.DEFAULT_USER
            new_user.password = '123456'
            new_user.is_active = False
            new_user.save()

    def _on_connect(self, client, userdata, flags, rc):
        self.client.message_callback_add('$SYS/broker/connection/+/state',
                                         self._monitor_broker_bridges)
        self.client.subscribe('$SYS/broker/connection/+/state')
        self.client.message_callback_add('senders/+/sender/stats',
                                         self._monitor_for_new_stats)
        self.client.subscribe('senders/+/sender/stats')
        self.client.message_callback_add('devices/+/lamp/changed',
                                         self._monitor_lamp_state)
        self.client.subscribe('devices/+/lamp/changed')

    def _create_mqtt_client_and_loop_forever(self):
        self.client = Client()
        self.client.on_connect = self._on_connect
        self.client.connect('localhost', port=50001)
        self.client.loop_forever()

    def _monitor_for_new_stats(self, client, userdata, message):
        print("RECV: '{}' on '{}'".format(message.payload, message.topic))
        if message.payload == b'1':
            # broker connected
            results = re.search(MQTT_SENDER_STATS_RE_PATTERN,
                                message.topic.lower())
            device_id = results.group('device_id')
            try:
                device = SenderDevice.objects.get(device_id=device_id)
                data = json.loads(message.payload.decode())
                
                # Parse timestamp
                timestamp = datetime.strptime(data['timestamp'],
                                              '%Y-%m-%d %H:%M:%S')
                
                # Create DeviceData entry
                device_data = DeviceData.objects.create(
                    device=device,
                    timestamp=timestamp,
                    kbmemfree=data['memory']['kbmemfree'],
                    kbmemused=data['memory']['kbmemused'],
                    memused_percent=data['memory']['memused_percent'],
                    cputemp=data['cpu']['temperature']
                )
                
                # Process disk stats
                for disk in data['disks']:
                    DiskStats.objects.create(
                        device_data=device_data,
                        device=disk['device'],
                        wait=disk['wait'],
                        util=disk['util']
                    )
                
                # Process CPU loads
                for core, load in enumerate(data['cpu']['loads']):
                    CpuLoad.objects.create(
                        device_data=device_data,
                        core=core,
                        load=load
                    )
                
                # Process network stats
                for net in data['network']:
                    NetworkStats.objects.create(
                        device_data=device_data,
                        iface=net['iface'],
                        rx_kb=net['rx_kb'],
                        tx_kb=net['tx_kb']
                    )
                
                print(f"Processed data from {device_id} at {timestamp}")
            
            except Exception as e:
                print(f"Error processing message: {e}")

    def _monitor_for_new_devices(self, client, userdata, message):
        print("RECV: '{}' on '{}'".format(message.payload, message.topic))
        # message payload has to treated as type "bytes" in Python 3
        if message.payload == b'1':
            # broker connected
            results = re.search(MQTT_BROKER_RE_PATTERN, message.topic.lower())
            if results:
                device_id = results.group('device_id')
                try:
                    device = Lampi.objects.get(device_id=device_id)
                    print("Found {}".format(device))
                except Lampi.DoesNotExist:
                    # this is a new device - create new record for it
                    new_device = Lampi(device_id=device_id)
                    uname = settings.DEFAULT_USER
                    new_device.user = User.objects.get(username=uname)
                    new_device.save()
                    print("Created {}".format(new_device))
                    # send association MQTT message
                    new_device.publish_unassociated_msg()
            else:
                results = re.search(MQTT_SENDER_BROKER_RE_PATTERN,
                                    message.topic.lower())
                device_id = results.group('device_id')
                try:
                    device = SenderDevice.objects.get(device_id=device_id)
                    print("Found {}".format(device))
                except SenderDevice.DoesNotExist:
                    # this is a new device - create new record for it
                    new_device = SenderDevice(device_id=device_id)
                    uname = settings.DEFAULT_USER
                    new_device.user = User.objects.get(username=uname)
                    new_device.save()
                    print("Created {}".format(new_device))
                    # send association MQTT message
                    new_device.publish_unassociated_msg()
                    
    def _monitor_broker_bridges(self, client, userdata, message):
        self._monitor_for_new_devices(client, userdata, message)
        self._monitor_for_connection_events(client, userdata, message)

    def _monitor_for_connection_events(self, client, userdata, message):
        results = re.search(MQTT_BROKER_RE_PATTERN, message.topic.lower())
        device_id = results.group('device_id')
        connection_state = 'unknown'
        if message.payload == b'1':
            print("DEVICE {} CONNECTED".format(device_id))
            connection_state = 'Connected'
        else:
            print("DEVICE {} DISCONNECTED".format(device_id))
            connection_state = 'Disconnected'
        self.mp.track('mqttbridge', "LAMPI {}".format(connection_state),
                      {
                            'event_type': 'devicemonitoring',
                            'interface': 'mqtt',
                            'device_id': device_id
                      }
                      )

    def _monitor_lamp_state(self, client, userdata, message):
        results = re.search(DEVICE_STATE_RE_PATTERN, message.topic.lower())
        device_id = results.group('device_id')
        event_props = {'event_type': 'devicestate',
                       'interface': 'mqtt', 'device_id': device_id}
        event_props.update(json.loads(message.payload.decode('utf-8')))

        self.mp.track('mqttbridge', 'LAMPI State Change', event_props)

    def handle(self, *args, **options):
        self.mp = Mixpanel(settings.MIXPANEL_TOKEN)

        self._create_default_user_if_needed()
        self._create_mqtt_client_and_loop_forever()
