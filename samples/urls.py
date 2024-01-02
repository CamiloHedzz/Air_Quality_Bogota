from django.urls import path, include
from rest_framework import routers
from samples import views

router = routers.DefaultRouter()
router.register(r'sample', views.SampleView, 'sample' )

urlpatterns = [
    path('apisample/v1/', include(router.urls))
]
