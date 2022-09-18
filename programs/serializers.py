from rest_framework import serializers

from .models import Programs


class ProgramsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programs
        fields = ('id', 'program_info',)


class ProgramsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programs
        fields = ('id', 'program_info',)
