from django.db import models
from samples.models import Sample
from event.models import Event

# Create your models here.

class Rute(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration = models.DurationField()
    id_sample = models.OneToOneField(Sample, on_delete=models.CASCADE, null=True)
    id_event = models.OneToOneField(Event, on_delete=models.CASCADE, null=True)
