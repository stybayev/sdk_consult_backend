from django.contrib import admin
from real_estate.models import RealEstate, CityDistricts, Images


class RealEstateAdmin(admin.ModelAdmin):
    list_display = (
        'real_estate_type',
        'district_city',
        'price',
        'subject_to_mortgage',
        'primary_secondary',
        'year_of_construction',
        'floor',
        'presence_balcony',
        'glazed_balcony',
        'number_of_bathrooms',
        'number_of_square_meters',
        'current_state')

    list_filter = ['district_city',
                   'real_estate_type',
                   'number_of_rooms',
                   'primary_secondary',
                   'year_of_construction']


class CityDistrictsAdmin(admin.ModelAdmin):
    list_display = ['title', ]


class ImagesAdmin(admin.ModelAdmin):
    list_display = ['image', ]


admin.site.register(RealEstate, RealEstateAdmin)
admin.site.register(CityDistricts, CityDistrictsAdmin)
admin.site.register(Images, ImagesAdmin)
