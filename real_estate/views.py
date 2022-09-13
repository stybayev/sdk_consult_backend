from rest_framework.response import Response
from rest_framework import status, views, permissions, generics

from authentication import messages
from real_estate.models import RealEstate
from real_estate.serializers import RealEstateSerializer, RealEstateDetailSerializer, RealEstateCreateSerializer


class RealEstateListView(views.APIView):
    def get(self, request):
        real_estate = RealEstate.objects.all()
        serializer = RealEstateSerializer(real_estate, many=True)
        return Response(serializer.data)


class RealEstateDetailView(views.APIView):
    def get(self, request, pk):
        try:
            real_estate = RealEstate.objects.get(id=self.kwargs.get('pk', None))
            serializer = RealEstateDetailSerializer(real_estate)
            return Response(serializer.data)
        except RealEstate.DoesNotExist:
            return Response(
                {'error': {'message': f'Мы не нашли ничего по вашему запросу!',
                           'status_code': status.HTTP_404_NOT_FOUND},

                 },
                status=status.HTTP_400_BAD_REQUEST)


class RealEstateCreateView(generics.GenericAPIView):
    serializer_class = RealEstateCreateSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
