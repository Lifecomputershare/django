from django.utils.deprecation import MiddlewareMixin


class UserAuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            from api.models import UserAuditLog
        except Exception:
            return response
        user = getattr(request, "user", None)
        try:
            UserAuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                ip_address=request.META.get("REMOTE_ADDR", ""),
            )
        except Exception:
            return response
        return response

