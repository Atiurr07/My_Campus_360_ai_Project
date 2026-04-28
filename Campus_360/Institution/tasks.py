from celery  import shared_task
from django.utils import timezone
from .models import QueueToken
from .fcm import send_push_to_user
from django.db.models import Count, Avg
import datetime


@shared_task
def notify_near_token():
    """
    Find tokens where waiting count <= 2 and fcm_sent=False and status waiting.
    Send push to user.
    """

    services = set(QueueToken.objects.values_list('service', flat=True))
    for t in QueueToken.objects.filter(status=QueueToken.STATUS_WAITING, fcm_sent =False):
        waiting = QueueToken.objects.filter(service=t.service, status__in=[QueueToken.STATUS_WAITING, QueueToken.STATUS_ACTIVE], token_number__lt=t.token_number).count()
        if waiting <=2:
            send_push_to_user(t.user, f"Your turn is near: #{t.token_number}", f"{waiting} ahead for {t.service.name}", data={"token_id": str(t.id)})
            t.fcm_sent= True
            t.save()


@shared_task
def cleanup_expired_token(expire_minutes=120):
    cutoff = timezone.now() - datetime.timedelta(minutes=expire_minutes)

    # mark waiting tokens older than cutoff as missed
    qs = QueueToken.objects.filter(status=QueueToken.STATUS_WAITING, created_at__lt=cutoff)
    qs.update(status=QueueToken.STATUS_MISSED)

@shared_task
def compute_analytics():
    #  for eg:: average service time per service

    from django.db.models import F, ExpressionWrapper, DurationField
    served = QueueToken.objects.filter(status=QueueToken.STATUS_SERVED).annotate(
        duration=ExpressionWrapper(F('served_at') - F('started_at'), output_field=DurationField())
    ).values('service__name').annotate(avg_duration=Avg('duration'), total=Count('id'))

    # store result in cach or DB fro admin cinsumption
    return list(served)
