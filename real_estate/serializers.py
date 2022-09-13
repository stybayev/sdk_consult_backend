from rest_framework import serializers

from real_estate.models import RealEstate, CityDistricts, Images


class ChoiceField(serializers.ChoiceField):

    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices[obj]

    def to_internal_value(self, data):
        if data == '' and self.allow_blank:
            return ''

        for key, val in self._choices.items():
            if val == data:
                return key
        self.fail('invalid_choice', input=data)


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


class RealEstateCreateSerializer(serializers.ModelSerializer):
    district_city = serializers.CharField(max_length=128, min_length=6, )
    real_estate_type = ChoiceField(choices=RealEstate.REAL_ESTATE_TYPE_CHOICES)
    primary_secondary = ChoiceField(choices=RealEstate.PRIMARY_SECONDARY_CHOICES)
    glazed_balcony = ChoiceField(choices=RealEstate.GLAZED_BALCONY_CHOICES)

    class Meta:
        model = RealEstate
        fields = ('district_city', 'real_estate_type', 'price', 'number_of_rooms',
                  'subject_to_mortgage', 'primary_secondary', 'year_of_construction',
                  'floor', 'presence_balcony', 'glazed_balcony', 'number_of_bathrooms',
                  'number_of_square_meters', 'current_state', 'description')

    def create(self, validated_data):
        district_city = validated_data.pop('district_city')
        district_city_instance, created = CityDistricts.objects.get_or_create(title=district_city)
        self.real_estate = RealEstate.objects.create(**validated_data, district_city=district_city_instance)
        self.real_estate.save()
        return self.real_estate
