from rest_framework.response import Response
from rest_framework import status, permissions, generics

from favorites.serializers import (AddFavoriteSerializer, UserFavoriteListSerializer, RemoveFavoriteSerializer)
from real_estate.models import RealEstate
from real_estate.serializers import (RealEstateSerializer, )


class AddFavoriteView(generics.GenericAPIView):
    serializer_class = AddFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = request.user
            real_estate = RealEstate.objects.get(id=request.data.get('id', None))
            user.favorite.add(real_estate)

            return Response({'success': f'Объявление успешно добавлено в избранное',
                             'status_code': status.HTTP_200_OK},
                            status=status.HTTP_200_OK)
        except RealEstate.DoesNotExist:
            return Response({
                'error': {
                    'status_code': status.HTTP_404_NOT_FOUND,
                    'message': 'Недвижимость не существует'}},
                status=status.HTTP_404_NOT_FOUND)

        except Exception as message:
            error_type = type(message).__name__
            return Response(
                {'error': {'error_type': f'{error_type}',
                           'message': f'{message}',
                           'status_code': status.HTTP_400_BAD_REQUEST},
                 },
                status=status.HTTP_400_BAD_REQUEST)


class UserFavoriteListView(generics.GenericAPIView):
    serializer_class = UserFavoriteListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_favorites = user.favorite.all()

        serializer_favorite = RealEstateSerializer(user_favorites, many=True)

        return Response({'favorites': serializer_favorite.data},
                        status=status.HTTP_200_OK)


class RemoveFavoriteView(generics.GenericAPIView):
    serializer_class = RemoveFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = request.user
            real_estate = RealEstate.objects.get(id=request.data.get('id', None))
            user.favorite.remove(real_estate)

            return Response({'success': f'Объявление успешно удалено из избранных',
                             'status_code': status.HTTP_200_OK},
                            status=status.HTTP_200_OK)
        except RealEstate.DoesNotExist:
            return Response({
                'error': {
                    'status_code': status.HTTP_404_NOT_FOUND,
                    'message': 'Недвижимость не существует'}},
                status=status.HTTP_404_NOT_FOUND)

        except Exception as message:
            error_type = type(message).__name__
            return Response(
                {'error': {'error_type': f'{error_type}',
                           'message': f'{message}',
                           'status_code': status.HTTP_400_BAD_REQUEST},
                 },
                status=status.HTTP_400_BAD_REQUEST)
