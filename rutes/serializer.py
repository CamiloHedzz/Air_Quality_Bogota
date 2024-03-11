from rest_framework import serializers
from .models import Rute

class RuteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rute
        fields = '__all__'
    