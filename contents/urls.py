from django.urls import path

from . import views

"""
Список урлов приложения content
"""
urlpatterns = [
    path('news_list/', views.NewsArticleListView.as_view(), name='news_list'),
    path('news_detail/<int:pk>/', views.NewsArticleDetailView.as_view(), name='news_detail'),
]
