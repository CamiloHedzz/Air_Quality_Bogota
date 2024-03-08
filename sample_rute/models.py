from django.db import models
from samples.models import Sample
from rutes.models import Rute

# Create your models here.
class Sample_rute(models.Model):
    id_sample_rute = models.AutoField(primary_key=True)
    #sample = models.ForeignKey(Sample.id_sample, on_delete=models.CASCADE)
    #rute = models.ForeignKey(Rute.id_rute, on_delete=models.CASCADE)