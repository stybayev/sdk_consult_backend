from django.contrib import admin
from .models import Programs


class ProgramsAdmin(admin.ModelAdmin):
    list_display = ('title', 'descriptions')


admin.site.register(Programs, ProgramsAdmin)
