from django.contrib import admin
from .models import Programs
from parler.admin import TranslatableAdmin


class ProgramsAdmin(admin.ModelAdmin):
    list_display = ('title', 'descriptions')


admin.site.register(Programs, TranslatableAdmin)
