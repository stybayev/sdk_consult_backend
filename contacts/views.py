from rest_framework.response import Response
from rest_framework import generics, status, views, permissions
from contacts.models import ContactsForCommunication
from contacts.serializers import ContactListSerializer, ContactDetailSerializer


class ContactListView(views.APIView):
    def get(self, request):
        try:
            contacts = ContactsForCommunication.objects.all()
            serializer = ContactListSerializer(contacts, many=True)
            return Response(serializer.data)
        except ContactsForCommunication.DoesNotExist:
            return Response(
                {
                    'error': {
                        'field': 'country_iso_code',
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'По вашему запросу ничего не нашли!'}
                },
                status=status.HTTP_404_NOT_FOUND)


class ContactDetailView(views.APIView):
    def get(self, request, pk):
        try:
            contacts = ContactsForCommunication.objects.get(id=pk)
            serializer = ContactDetailSerializer(contacts)
            return Response(serializer.data)
        except ContactsForCommunication.DoesNotExist:
            return Response(
                {
                    'error': {
                        'field': 'country_iso_code',
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'Контакт с данным id не существует!'}
                },
                status=status.HTTP_404_NOT_FOUND)
