from django.db import models
from django.conf import settings

MainUser = settings.AUTH_USER_MODEL

# Create your models here.
# 1. model for Meeting::
class Meeting(models.Model):
    user= models.ForeignKey(MainUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    transcript = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null = True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

# 2. Models for Note::
class Note(models.Model):
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    tags = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


# 3. Models for SentimentRecord::
class SentimentRecord(models.Model):
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    text = models.TextField()
    sentiment = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)