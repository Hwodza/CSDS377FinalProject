from django.apps import AppConfig


class AggregatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aggregator'

    def ready(self):
        # Import the MQTT client and start it
        from .mqtt_client import start_mqtt
        start_mqtt()