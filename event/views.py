from django.shortcuts import render
from .serializer import EventSerializer
from .models import Event
from rest_framework import viewsets
# Create your views here.
class EventView(viewsets.ModelViewSet): 
    serializer_class = EventSerializer
    queryset = Event.objects.all()