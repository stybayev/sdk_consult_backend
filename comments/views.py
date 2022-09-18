from rest_framework.response import Response
from rest_framework import generics, status, views, permissions
from comments.models import Comment
from comments.serializers import (CommentListSerializer, CommentDetailSerializer,
                                  CommentCreateSerializer, CommentDetailCreateSerializer)
from real_estate.models import RealEstate


class CommentListView(views.APIView):
    def get(self, request):
        try:
            comment = Comment.objects.all()
            serializer = CommentListSerializer(comment, many=True)
            return Response(serializer.data)
        except Comment.DoesNotExist:
            return Response(
                {
                    'error': {
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'По вашему запросу ничего не нашли!'}
                },
                status=status.HTTP_404_NOT_FOUND)


class CommentDetailView(views.APIView):
    def get(self, request, pk):
        try:
            comment = Comment.objects.get(id=pk)
            serializer = CommentDetailSerializer(comment)
            return Response(serializer.data)
        except Comment.DoesNotExist:
            return Response(
                {
                    'error': {
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'Отзыв с данным id не существует!'}
                },
                status=status.HTTP_404_NOT_FOUND)


class CommentCreateView(generics.GenericAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        real_estate = RealEstate.objects.get(id=serializer.data.get('real_estate'))
        text = serializer.data.get('text')
        comment = Comment.objects.create(
            author_id=request.user.id,
            real_estate=real_estate,
            text=text)

        response = CommentDetailCreateSerializer(comment)
        return Response(response.data, status=status.HTTP_201_CREATED)
