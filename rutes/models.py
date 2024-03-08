from django.db import models
from samples.models import Sample
#from sample_rute.models import Sample_rute
# Create your models here.

class Rute(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration = models.DurationField()
 #   samples = models.ManyToManyField(Sample, through=Sample_rute)