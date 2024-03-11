from django.urls import path, include
from rest_framework import routers
from event import views

router = routers.DefaultRouter()
router.register(r'event', views.EventView, 'event' )

urlpatterns = [
    path('apievent/v1/', include(router.urls))
]
