from django.shortcuts import render
from .serializer import RuteSerializer
from .models import Rute
from rest_framework import viewsets
# Create your views here.
class RuteView(viewsets.ModelViewSet): 
    serializer_class = RuteSerializer
    queryset = Rute.objects.all()