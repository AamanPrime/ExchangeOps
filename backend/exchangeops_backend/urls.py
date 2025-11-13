from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from monitoring.views import ExchangeViewSet, ConnectionEventViewSet, IncidentViewSet
from audit.views import AuditLogViewSet

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'exchanges', ExchangeViewSet)
router.register(r'connection-events', ConnectionEventViewSet)
router.register(r'incidents', IncidentViewSet)
router.register(r'audit-logs', AuditLogViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
]
