from rest_framework import serializers

from .models import Services


class ServicesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ('id', 'service_info',)


class ServicesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ('id', 'service_info',)
