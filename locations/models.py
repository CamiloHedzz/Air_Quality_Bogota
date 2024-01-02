from django.db import models

# Create your models here.

class Location(models.Model):
    id = models.AutoField(primary_key=True)
    location_id = models.IntegerField()
    location_name = models.CharField(max_length=500)
    #neighboorhood, city, ...
    
    def __str__(self):
        return f'Location {self.id}: {self.location_name}'