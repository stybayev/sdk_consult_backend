from django.contrib.auth import get_user_model
from rest_framework import serializers

from real_estate.models import RealEstate
from .models import Comment


class AuthorCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'last_name', 'first_name', 'avatar')


class RealEstateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealEstate
        fields = ('id', 'real_estate_info')


class CommentListSerializer(serializers.ModelSerializer):
    author = AuthorCommentSerializer(read_only=True)
    real_estate = RealEstateSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'real_estate', 'author')


class CommentDetailSerializer(serializers.ModelSerializer):
    author = AuthorCommentSerializer(read_only=True)
    real_estate = RealEstateSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'real_estate', 'author')


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['text', 'real_estate', 'author']
        read_only_fields = ['author']


class CommentDetailCreateSerializer(serializers.ModelSerializer):
    author = AuthorCommentSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author')
