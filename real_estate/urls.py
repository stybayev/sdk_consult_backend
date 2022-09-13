from django.urls import path

from . import views

urlpatterns = [
    path('real_estate_list/', views.RealEstateListView.as_view(), name='real_estate_list'),
    path('real_estate_detail/<int:pk>/', views.RealEstateDetailView.as_view(), name='real_estate_detail'),
    path('create_real_estate/', views.RealEstateCreateView.as_view(), name='create_real_estate'),
]
