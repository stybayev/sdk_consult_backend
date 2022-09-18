from django.shortcuts import render
from django.utils.translation import get_language

from rest_framework.response import Response
from rest_framework import generics, status, views, permissions

from .models import NewsArticle
from .serializers import NewsArticleListSerializer, NewsArticleDetailSerializer


class NewsArticleListView(views.APIView):
    def get(self, request):
        try:
            news_articles = NewsArticle.objects.language(get_language()).all()
            serializer = NewsArticleListSerializer(news_articles, many=True)
            return Response(serializer.data)
        except NewsArticle.DoesNotExist:
            return Response(
                {
                    'error': {
                        'field': 'country_iso_code',
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'По вашему запросу ничего не нашли!'}
                },
                status=status.HTTP_404_NOT_FOUND)


class NewsArticleDetailView(views.APIView):
    def get(self, request, pk):
        try:
            news_article = NewsArticle.objects.language(get_language()).get(id=pk)
            serializer = NewsArticleDetailSerializer(news_article)
            return Response(serializer.data)
        except NewsArticle.DoesNotExist:
            return Response(
                {
                    'error': {
                        'field': 'country_iso_code',
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'Новости с данным id не существует!'}
                },
                status=status.HTTP_404_NOT_FOUND)
