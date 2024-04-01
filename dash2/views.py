from django.shortcuts import render
from dash2 import dash_app
from dash2 import app

# Create your views here.

def dash_view(request):    
    return render(request, 'dash_app.html')  
