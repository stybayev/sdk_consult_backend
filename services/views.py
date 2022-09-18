from rest_framework.response import Response
from rest_framework import views, status

from services.models import Services
from services.serializers import ServicesListSerializer, ServicesDetailSerializer


class ServicesListView(views.APIView):
    def get(self, request):
        news_articles = Services.objects.all()
        serializer = ServicesListSerializer(news_articles, many=True)
        return Response(serializer.data)


class ServicesDetailView(views.APIView):
    def get(self, request, pk):
        try:
            services = Services.objects.get(id=pk)
            serializer = ServicesDetailSerializer(services)
            return Response(serializer.data)
        except Services.DoesNotExist:
            return Response(
                {
                    'error': {
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'Услуга с данным id не существует!'}
                },
                status=status.HTTP_404_NOT_FOUND)
