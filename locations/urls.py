from django.urls import path, include
from rest_framework import routers
from locations import views

router = routers.DefaultRouter()
router.register(r'location', views.LocationView, 'location' )

urlpatterns = [
    path('apilocation/v1/', include(router.urls))
]
