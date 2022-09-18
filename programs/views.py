from django.shortcuts import render
from django.utils.translation import get_language
from rest_framework.response import Response
from rest_framework import generics, status, views, permissions

from programs.models import Programs
from programs.serializers import ProgramsListSerializer, ProgramsDetailSerializer


class ProgramsListView(views.APIView):
    def get(self, request):
        try:
            programs = Programs.objects.language(get_language()).all()
            serializer = ProgramsListSerializer(programs, many=True)
            return Response(serializer.data)
        except Programs.DoesNotExist:
            return Response(
                {
                    'error': {
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'По вашему запросу ничего не нашли!'}
                },
                status=status.HTTP_404_NOT_FOUND)


class ProgramsDetailView(views.APIView):
    def get(self, request, pk):
        try:
            program = Programs.objects.language(get_language()).get(id=pk)
            serializer = ProgramsDetailSerializer(program)
            return Response(serializer.data)
        except Programs.DoesNotExist:
            return Response(
                {
                    'error': {
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'message': f'Программы с данным id не существует!'}
                },
                status=status.HTTP_404_NOT_FOUND)
