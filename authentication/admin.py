from django.contrib import admin
from .models import (User, )


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'phone_number',
        'email_verified',
        'phone_verified',
        'first_name',
        'last_name',
    )

    list_filter = ['email', ]

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = \
            super().get_deleted_objects(objs, request)
        return deleted_objects, model_count, set(), protected


admin.site.register(User, UserAdmin)
