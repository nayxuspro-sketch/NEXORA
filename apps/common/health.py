from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.utils import timezone
import os


class HealthCheckView(APIView):
    """
    Service healthcheck endpoint for Docker, Kubernetes, and uptime monitoring.
    Verifies:
    - Web application server responsiveness
    - Database connection health
    - Timestamp & Environment mode
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'database': 'unknown',
            'environment': 'development' if os.environ.get('DJANGO_DEBUG', 'True') == 'True' else 'production'
        }

        # Check DB connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    health_status['database'] = 'connected'
                else:
                    health_status['database'] = 'unexpected_result'
                    health_status['status'] = 'degraded'
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health_status, status=status.HTTP_200_OK)
