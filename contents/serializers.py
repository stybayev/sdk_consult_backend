from rest_framework import serializers

from .models import NewsArticle


class NewsArticleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = ('id', 'article_info',)


class NewsArticleDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = ('id', 'article_info',)
