from django.urls import path

from . import views

urlpatterns = [
    path('program_list/', views.ProgramsListView.as_view(), name='program_list'),
    path('program_detail/<int:pk>/', views.ProgramsDetailView.as_view(), name='program_detail'),
]
