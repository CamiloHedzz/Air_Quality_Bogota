from django.db import models
from locations.models import Location

# Create your models here.

class Sample(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=500)
    sample = models.IntegerField() #pm25 values should be here
    location = models.OneToOneField(Location, on_delete=models.CASCADE)    
    #sample_time
    
    def __str__(self):
        return f'Sample {self.id}: {self.name}'