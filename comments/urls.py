from django.urls import path

from . import views

urlpatterns = [
    path('comment_list/', views.CommentListView.as_view(), name='comment_list'),
    path('comment_detail/<int:pk>/', views.CommentDetailView.as_view(), name='comment_detail'),
    path('comment_create/', views.CommentCreateView.as_view(), name='comment_create'),
]
