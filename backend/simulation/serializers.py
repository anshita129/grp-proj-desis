from rest_framework import serializers
from .models import SimulationSession

class SimulationSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationSession
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
