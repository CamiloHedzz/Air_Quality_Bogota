from django.db import models


# Create your models here.

class Event(models.Model):
    id_event = models.AutoField(primary_key=True)
    dia_sin_carro = models.BooleanField(default=False)
    festividad = models.BooleanField(default=False)
    protesta = models.BooleanField(default=False)
    volumen_trafico = models.DecimalField(max_digits=6, decimal_places=2)