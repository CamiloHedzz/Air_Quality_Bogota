from django.shortcuts import render

# Create your views here.

def dash_view(request):
    return render(request, 'dash_app.html') 

def dash_view2(request):
    return render(request, 'dash_app2.html')