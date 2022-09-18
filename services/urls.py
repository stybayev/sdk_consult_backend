from django.urls import path

from . import views

urlpatterns = [
    path('services_list/', views.ServicesListView.as_view(), name='services_list'),
    path('services_detail/<int:pk>/', views.ServicesDetailView.as_view(), name='services_detail'),
]
