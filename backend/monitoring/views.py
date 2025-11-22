from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Exchange, ConnectionEvent, Incident
from .serializers import ExchangeSerializer, ConnectionEventSerializer, IncidentSerializer
from audit.models import AuditLog
import requests
from exchangeops_backend.settings import SIMULATOR_URL

class ExchangeViewSet(viewsets.ModelViewSet):
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer

    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        exchange = self.get_object()
        try:
            resp = requests.post(f"{SIMULATOR_URL}/exchanges/{exchange.name}/restart", timeout=2)
            if resp.status_code == 200:
                # Log audit
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action="RESTART_EXCHANGE",
                    target=exchange.name,
                    metadata={"status": "success"}
                )
                # Resolve incident if exists
                open_incident = Incident.objects.filter(exchange=exchange, resolved_at__isnull=True).first()
                if open_incident:
                    open_incident.resolved_at = timezone.now()
                    open_incident.resolved_by = request.user if request.user.is_authenticated else None
                    open_incident.save()

                return Response({'status': 'restarted'})
            else:
                return Response({'error': 'Simulator returned error'}, status=resp.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ConnectionEventViewSet(viewsets.ModelViewSet):
    queryset = ConnectionEvent.objects.all().order_by('-recorded_at')
    serializer_class = ConnectionEventSerializer
    filterset_fields = ['exchange', 'status']

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all().order_by('-opened_at')
    serializer_class = IncidentSerializer
    filterset_fields = ['exchange', 'severity']

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter == 'open':
            return qs.filter(resolved_at__isnull=True)
        elif status_filter == 'resolved':
            return qs.filter(resolved_at__isnull=False)
        return qs
