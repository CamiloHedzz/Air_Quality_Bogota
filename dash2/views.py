from django.shortcuts import render
from django.http import JsonResponse
from dash2 import dash_app
from dash2.dash_app import app
# Create your views here.

def dash_view(request):
    return render(request, 'dash_app.html')  

def dash_view2(request):
    return render(request, 'dash_app2.html')