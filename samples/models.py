from django.db import models

# Create your models here.

class Sample(models.Model):
    id_sample = models.AutoField(primary_key=True)
    name = models.CharField(max_length=500)
    date = models.DateTimeField()
    longitude = models.FloatField()
    latitude = models.FloatField()
    value_PM2 = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    neighbourhood = models.CharField(max_length=100)
    
    def __str__(self):
        return f'Sample {self.id_sample}: {self.name}'