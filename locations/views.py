from rest_framework import viewsets
from .serializer import LocationSerializer
from .models import Location

# Create your views here.

class LocationView(viewsets.ModelViewSet): 
    serializer_class = LocationSerializer
    queryset = Location.objects.all()