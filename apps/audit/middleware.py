import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from apps.audit.models import AuditLog

logger = logging.getLogger('nexora.security')


class SecurityAuditLoggingMiddleware(MiddlewareMixin):
    """
    Automatic security audit logging middleware.
    Consigns:
    - User logins & authentication events
    - Sensitive mutating actions (POST, PUT, PATCH, DELETE)
    - Source IP, user identity, company tenant, resource path and status code
    - Failed authentication / permission denied attempts (401, 403)
    """

    def process_response(self, request, response):
        try:
            # We only track API endpoints
            if not request.path.startswith('/api/v1/'):
                return response

            user = getattr(request, 'user', None)
            is_authenticated = user and user.is_authenticated
            company = getattr(user, 'company', None) if is_authenticated else None

            method = request.method
            status_code = response.status_code
            ip_address = self._get_client_ip(request)

            # 1. Track Authentication events (/auth/token/)
            if '/auth/token/' in request.path and method == 'POST':
                if status_code == 200:
                    try:
                        resp_data = json.loads(response.content)
                        user_info = resp_data.get('user', {})
                        from apps.companies.models import Company
                        user_company = None
                        if user_info.get('company_id'):
                            user_company = Company.objects.filter(id=user_info['company_id']).first()

                        if user_company:
                            AuditLog.objects.create(
                                company=user_company,
                                action='LOGIN_SUCCESS',
                                resource_type='Authentication',
                                resource_id=user_info.get('id', ''),
                                user_id=user_info.get('id'),
                                ip_address=ip_address,
                                details={'email': user_info.get('email'), 'role': user_info.get('role')}
                            )
                    except Exception as e:
                        logger.error(f"Failed to log login event: {e}")

                elif status_code in (400, 401):
                    logger.warning(f"Failed login attempt from IP {ip_address}")

            # 2. Track Unauthorized / Forbidden Attempts (401, 403)
            elif status_code in (401, 403) and is_authenticated and company:
                AuditLog.objects.create(
                    company=company,
                    action='PERMISSION_DENIED_ATTEMPT',
                    resource_type='SecurityAlert',
                    resource_id=request.path,
                    user=user,
                    ip_address=ip_address,
                    details={'method': method, 'path': request.path, 'status_code': status_code}
                )

            # 3. Track Mutating Business Actions (POST, PUT, PATCH, DELETE) for authenticated tenant users
            elif method in ['POST', 'PUT', 'PATCH', 'DELETE'] and is_authenticated and company:
                # Exclude chat polling if trivial
                if '/ai/chat/' in request.path:
                    return response

                action_label = f"{method}_{request.path.strip('/').split('/')[-1].upper()}"
                resource_type = request.path.strip('/').split('/')[2] if len(request.path.strip('/').split('/')) > 2 else 'API'

                AuditLog.objects.create(
                    company=company,
                    action=action_label[:50],
                    resource_type=resource_type[:50],
                    resource_id=request.path[:100],
                    user=user,
                    ip_address=ip_address,
                    details={'status_code': status_code}
                )

        except Exception as e:
            logger.error(f"Audit middleware exception: {e}")

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
