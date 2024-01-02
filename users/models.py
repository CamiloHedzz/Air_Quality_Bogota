from django.db import models
from samples.models import Sample

# Create your models here.

class User(models.Model):
    id = models.AutoField(primary_key=True)
    identification = models.IntegerField()
    name = models.CharField(max_length=500)
    last_name = models.CharField(max_length=500)
    sample = models.ForeignKey(Sample,on_delete=models.SET_NULL,null=True )

    def __str__(self):
        return f'User {self.identification}: {self.name}'
        #return f'Localizacion {self.id}: {self.localizacion}: {self.active}'