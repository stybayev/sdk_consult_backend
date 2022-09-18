from django.contrib import admin
from .models import Services


class ServicesAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'order_service',)


admin.site.register(Services, ServicesAdmin)
