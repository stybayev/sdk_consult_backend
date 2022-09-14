from rest_framework import serializers
from real_estate.models import RealEstate, CityDistricts, Images
from django.contrib.auth import get_user_model


class AddFavoriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(write_only=True)

    class Meta:
        model = RealEstate
        fields = ['id', ]


class UserFavoriteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = []


class RemoveFavoriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(write_only=True)

    class Meta:
        model = RealEstate
        fields = ['id', ]
