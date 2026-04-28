from django.db import models
from django.conf import settings

MainUser = settings.AUTH_USER_MODEL

# Create your models here.

class ChatLog(models.Model):
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='chatlog')
    user_message = models.TextField()
    bot_response = models.TextField(blank=True, null=True)
    sentiment= models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add= True)

class SymptomLog(models.Model):
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    symptoms_text = models.TextField()
    result = models.JSONField(blank=True, null=True) # diagnosis suggestions
    created_at = models.DateTimeField(auto_now_add=True)


class SleepLog(models.Model):
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    sleep_hours = models.FloatField()
    quality = models.CharField(max_length=50, blank=True, null=True)
