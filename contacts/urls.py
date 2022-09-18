from django.urls import path

from contacts import views

urlpatterns = [
    path('contact_list/', views.ContactListView.as_view(), name='contact_list'),
    path('contact_detail/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
]
