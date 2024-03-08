from django.db import models
from event.models import Event

# Create your models here.

class Sample(models.Model):
    id_sample = models.AutoField(primary_key=True)
    name = models.CharField(max_length=500)
    date = models.DateField()
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    value_PM2 = models.DecimalField(max_digits=6, decimal_places=6)
    temperature = models.DecimalField(max_digits=6, decimal_places=6)
    humidity = models.DecimalField(max_digits=6, decimal_places=6)   
    neighbourhood = models.CharField(max_length=100)
    #id_evet = models.ForeignKey(Event , on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f'Sample {self.id_sample}: {self.name}'