from rest_framework import serializers
from .models import Exchange, ConnectionEvent, Incident

class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = '__all__'

class ConnectionEventSerializer(serializers.ModelSerializer):
    exchange_name = serializers.CharField(source='exchange.name', read_only=True)

    class Meta:
        model = ConnectionEvent
        fields = '__all__'

class IncidentSerializer(serializers.ModelSerializer):
    exchange_name = serializers.CharField(source='exchange.name', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)

    class Meta:
        model = Incident
        fields = '__all__'
