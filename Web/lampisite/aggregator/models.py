from django.db import models


# Create your models here.
class SystemData(models.Model):
    topic = models.CharField(max_length=255)
    payload = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.topic}: {self.payload[:50]}"
