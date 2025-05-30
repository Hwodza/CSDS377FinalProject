# Generated by Django 5.0.1 on 2025-04-27 20:42

import django.db.models.deletion
import lampi.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lampi', '0004_alter_lampi_device_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SenderDevice',
            fields=[
                ('name', models.CharField(default='My Sender', max_length=50)),
                ('device_id', models.CharField(db_index=True, max_length=12,
                                               primary_key=True,
                                               serialize=False)),
                ('association_code',
                 models.CharField(
                     default=lampi.models.generate_association_code,
                     max_length=32, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=models.SET(lampi.models.get_parked_user),
                    to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DeviceData',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('kbmemfree', models.IntegerField()),
                ('kbmemused', models.IntegerField()),
                ('memused_percent', models.FloatField()),
                ('cputemp', models.FloatField()),
                ('device', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='device_data', to='lampi.senderdevice')),
            ],
            options={
                'ordering': ['-timestamp'],
                'unique_together': {('device', 'timestamp')},
            },
        ),
        migrations.CreateModel(
            name='CpuLoad',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('core', models.IntegerField()),
                ('load', models.FloatField()),
                ('device_data', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cpu_loads', to='lampi.devicedata')),
            ],
            options={
                'unique_together': {('device_data', 'core')},
            },
        ),
        migrations.CreateModel(
            name='DiskStats',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('device', models.CharField(max_length=100)),
                ('wait', models.FloatField()),
                ('util', models.FloatField()),
                ('device_data', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='disk_stats', to='lampi.devicedata')),
            ],
            options={
                'unique_together': {('device_data', 'device')},
            },
        ),
        migrations.CreateModel(
            name='NetworkStats',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('iface', models.CharField(max_length=50)),
                ('rx_kb', models.FloatField()),
                ('tx_kb', models.FloatField()),
                ('device_data', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='network_stats', to='lampi.devicedata')),
            ],
            options={
                'unique_together': {('device_data', 'iface')},
            },
        ),
    ]
