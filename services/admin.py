from django.contrib import admin
from .models import Services
from parler.admin import TranslatableAdmin


class ServicesAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'order_service',)


admin.site.register(Services, TranslatableAdmin)
