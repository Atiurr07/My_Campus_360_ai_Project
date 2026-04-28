from pyfcm import FCMNotification
from django.conf import settings

def get_fcm():
    key = settings.FCM_SERVER_KEY
    return FCMNotification(api_key=key)

def send_push_to_user(user, title, body, data=None):
    from .models import MobileDevice
    try:
        dev = MobileDevice.objects.get(user=user)
        if not dev.fcm_token:
            return False
        push_service = get_fcm()
        result = push_service.notify_single_device(registration_id=dev.fcm_token, message_title = title, message_body= body, data_message = data or {})
        return result
    except MobileDevice.DoesNotExist:
        return False