from rest_framework import viewsets
from .serializer import SampleSerializer
from .models import Sample

# Create your views here.

class SampleView(viewsets.ModelViewSet): 
    serializer_class = SampleSerializer
    queryset = Sample.objects.all()