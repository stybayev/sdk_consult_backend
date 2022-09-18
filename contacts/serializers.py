from rest_framework import serializers

from .models import ContactsForCommunication


class ContactListSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactsForCommunication
        fields = ('id', 'contact_info',)


class ContactDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactsForCommunication
        fields = ('id', 'contact_info',)
