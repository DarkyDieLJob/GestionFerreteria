from django.db.models import Q
from .adapters.models import PasswordResetRequest


def staff_reset_requests_badge(request):
    """Adds pending_reset_requests_count for staff users.
    Counts requests that still require action under the new flow:
      - status pending
      - status under_review
      - status ready_to_deliver
    """
    count = 0
    try:
        if request.user.is_authenticated and request.user.is_staff:
            qs = PasswordResetRequest.objects.filter(
                status__in=["pending", "under_review", "ready_to_deliver"]
            )
            count = qs.count()
    except Exception:
        count = 0
    return {"pending_reset_requests_count": count}
