from django.shortcuts import render

# Create your views here.

def dash_view(request):
    return render(request, 'dash_app.html') 