from django.urls import path

from . import views

urlpatterns = [
    path('add_to_favorite/', views.AddFavoriteView.as_view(), name='add_to_favorite'),
    path('user_favorite_list_view/', views.UserFavoriteListView.as_view(), name='user_favorite_list_view'),
    path('remove_from_favorites/', views.RemoveFavoriteView.as_view(), name='remove_from_favorites'),
]
