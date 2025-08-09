from django.db.models import Q
from .adapters.models import PasswordResetRequest


def staff_reset_requests_badge(request):
    """Adds pending_reset_requests_count for staff users.
    Counts requests that still require action:
      - status pending, or
      - status approved and the associated user still must change password.
    """
    count = 0
    try:
        if request.user.is_authenticated and request.user.is_staff:
            qs = PasswordResetRequest.objects.select_related("user__core_profile").filter(
                Q(status="pending") | Q(status="approved", user__core_profile__must_change_password=True)
            )
            count = qs.count()
    except Exception:
        count = 0
    return {"pending_reset_requests_count": count}
