from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4
import json
import paho.mqtt.publish

# Create your models here.
DEFAULT_USER = 'parked_device_user'


def get_parked_user():
    return get_user_model().objects.get_or_create(username=DEFAULT_USER)[0]


def generate_association_code():
    return uuid4().hex


class Lampi(models.Model):
    name = models.CharField(max_length=50, default="My LAMPI")
    device_id = models.CharField(db_index=True,
                                 max_length=12,
                                 primary_key=True)
    user = models.ForeignKey(User, db_index=True,
                             on_delete=models.SET(get_parked_user))
    association_code = models.CharField(max_length=32, unique=True,
                                        default=generate_association_code)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}: {}".format(self.device_id, self.name)

    def _generate_device_association_topic(self):
        return 'devices/{}/lamp/associated'.format(self.device_id)

    def publish_unassociated_msg(self):
        # send association MQTT message
        assoc_msg = {}
        assoc_msg['associated'] = False
        assoc_msg['code'] = self.association_code
        paho.mqtt.publish.single(
            self._generate_device_association_topic(),
            json.dumps(assoc_msg),
            qos=2,
            retain=True,
            hostname="localhost",
            port=50001,
            )

    def associate_and_publish_associated_msg(self,  user):
        # update Lampi instance with new user
        self.user = user
        self.save()
        # publish associated message
        assoc_msg = {}
        assoc_msg['associated'] = True
        paho.mqtt.publish.single(
            self._generate_device_association_topic(),
            json.dumps(assoc_msg),
            qos=2,
            retain=True,
            hostname="localhost",
            port=50001,
            )


class SenderDevice(models.Model):
    name = models.CharField(max_length=50, default="My Sender")
    device_id = models.CharField(db_index=True,
                                 max_length=12,
                                 primary_key=True)
    user = models.ForeignKey(User, db_index=True,
                             on_delete=models.SET(get_parked_user))
    association_code = models.CharField(max_length=32, unique=True,
                                        default=generate_association_code)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}: {}".format(self.device_id, self.name)

    def _generate_device_association_topic(self):
        return 'senders/{}/sender/associated'.format(self.device_id)

    def publish_unassociated_msg(self):
        # send association MQTT message
        assoc_msg = {}
        assoc_msg['associated'] = False
        assoc_msg['code'] = self.association_code
        paho.mqtt.publish.single(
            self._generate_device_association_topic(),
            json.dumps(assoc_msg),
            qos=2,
            retain=True,
            hostname="localhost",
            port=50001,
            )

    def associate_and_publish_associated_msg(self,  user):
        # update Lampi instance with new user
        self.user = user
        self.save()
        # publish associated message
        assoc_msg = {}
        assoc_msg['associated'] = True
        paho.mqtt.publish.single(
            self._generate_device_association_topic(),
            json.dumps(assoc_msg),
            qos=2,
            retain=True,
            hostname="localhost",
            port=50001,
            )


class DeviceData(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(SenderDevice,
                               on_delete=models.CASCADE,
                               related_name='data_points')
    timestamp = models.DateTimeField()
    kbmemfree = models.IntegerField()
    kbmemused = models.IntegerField()
    memused_percent = models.FloatField()
    cputemp = models.FloatField()

    class Meta:
        # Composite primary key
        unique_together = ('device', 'timestamp')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device.name} data at {self.timestamp}"


class DiskStats(models.Model):
    id = models.BigAutoField(primary_key=True)
    device_data = models.ForeignKey(DeviceData,
                                    on_delete=models.CASCADE,
                                    related_name='disk_stats')
    device = models.CharField(max_length=100)
    wait = models.FloatField()
    util = models.FloatField()

    class Meta:
        # Composite primary key
        unique_together = ('device_data', 'device')

    def __str__(self):
        return f"Disk {self.device} stats at {self.device_data.timestamp}"


class CpuLoad(models.Model):
    id = models.BigAutoField(primary_key=True)
    device_data = models.ForeignKey(DeviceData,
                                    on_delete=models.CASCADE,
                                    related_name='cpu_loads')
    core = models.IntegerField()
    load = models.FloatField()

    class Meta:
        # Composite primary key
        unique_together = ('device_data', 'core')

    def __str__(self):
        return f"Core {self.core} load at {self.device_data.timestamp}"


class NetworkStats(models.Model):
    id = models.BigAutoField(primary_key=True)
    device_data = models.ForeignKey(DeviceData,
                                    on_delete=models.CASCADE,
                                    related_name='network_stats')
    iface = models.CharField(max_length=50)
    rx_kb = models.FloatField()
    tx_kb = models.FloatField()

    class Meta:
        # Composite primary key
        unique_together = ('device_data', 'iface')

    def __str__(self):
        return f"Interface {self.iface} stats at {self.device_data.timestamp}"
