from rest_framework import serializers

from real_estate.models import RealEstate, CityDistricts, Images


class CityDistrictsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityDistricts
        fields = ('title',)


class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ('id', 'image')


class RealEstateSerializer(serializers.ModelSerializer):
    district_city = CityDistrictsSerializer()
    images = ImagesSerializer(many=True)

    class Meta:
        model = RealEstate
        fields = ('id',
                  'images',
                  'district_city',
                  'real_estate_info')


class RealEstateDetailSerializer(serializers.ModelSerializer):
    district_city = CityDistrictsSerializer()
    images = ImagesSerializer(many=True)

    class Meta:
        model = RealEstate
        fields = ('id',
                  'images',
                  'district_city',
                  'real_estate_info')
