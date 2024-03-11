from django.urls import path, include
from rest_framework import routers
from rutes import views

router = routers.DefaultRouter()
router.register(r'rutes', views.RuteView, 'rutes' )

urlpatterns = [
    path('apirute/v1/', include(router.urls))
]
