from django.contrib import admin
from .models import ContactsForCommunication


class ContactsForCommunicationAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'first_name', 'last_name', 'image')


admin.site.register(ContactsForCommunication, ContactsForCommunicationAdmin)
