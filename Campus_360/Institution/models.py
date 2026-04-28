from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
import uuid

MainUser = settings.AUTH_USER_MODEL

# Create your models here.
class Service(models.Model):
    name = models.CharField(max_length=120, unique=True)
    discription = models.TextField(blank=True)
    daily_limit = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class QueueToken(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_ACTIVE = 'active'
    STATUS_SERVED = 'served'
    STATUS_CANCELLED = 'cancelled'
    STATUS_MISSED = 'missed'

    STATUS_CHOICES = [
        (STATUS_WAITING , 'Waiting'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SERVED, 'Served'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_MISSED, 'Missed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey('Institution.Service', on_delete=models.CASCADE, related_name='tokens')
    token_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True)
    priority = models.BooleanField(default=False)
    qr_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  #QR identifier
    fcm_sent = models.BooleanField(default=False)  # sending notification nearly by user
    estimated_wait_minutes = models.IntegerField(null=True, blank=True) # stored snapshot


    class Meta:
        unique_together = ('service', 'token_number')
        ordering = ['service', 'token_number']

    def __str__(self):
            return f"{self.service.name} - Token #{self.token_number} ({self.get_status_display()})"

    def mark_served(self, by_user=None):
        self.status = self.STATUS_SERVED
        self.served_at = timezone.now()
        self.save()

        # hook :: call itegration with attendance system
        try:
            from .integrations import mark_attendance_for_token
            mark_attendance_for_token(self)
        except Exception:
            pass


    def mark_active(self):
        self.status = self.STATUS_ACTIVE
        self.started_at = timezone.now()
        self.save()

    def cancel(self):
        self.status = self.STATUS_CANCELLED
        self.save()

    @classmethod
    def create_next_token(cls, service, user=None, priority=False):
        """
        Atomic generation of next token_number for a given service.
        Use transaction + select_for_update on a small aggregate table to avoid race.
        """

        with transaction.atomic():

            s= Service.objects.select_for_update().get(pk=service.pk)
            last = cls.objects.filter(
                service=s,
                created_at__date=timezone.now().date()
                ).aggregate(models.Max('token_number'))['token_number__max'] or 0
            next_num = last+1
            token = cls.objects.create(
                user=user,
                service= s,
                token_number = next_num,
                priority=priority
            )
            return token

class MobileDevice(models.Model):
    user = models.OneToOneField(MainUser, on_delete= models.CASCADE)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now= True)


class Course(models.Model):
    name= models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    teacher = models.ForeignKey(MainUser, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    student = models.ManyToManyField(MainUser, related_name="enrolled_courses", limit_choices_to={'role': 'student'}, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class AttendanceRecord(models.Model):
    student = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='attendance')
    teacher = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='marked_attendance', null=True, blank=True, limit_choices_to={'role': 'teacher'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance', null=True, blank=True)
    date = models.DateField()
    period = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[('present', 'Present'), ('absent', 'Absent')])

    class Meta:
        unique_together = ('student', 'course', 'date', 'period')  # this is used for preventing the duplicate.

    def save(self, *args, **kwargs):
        if self.course:
            self.teacher = self.course.teacher
        super().save(*args, **kwargs)

    def __str__(self):
        course_code = self.course.code if self.course else "N/A"
        return f"{self.date} | {self.student.username} | {course_code} | Period {self.period} - {self.status}"

class FeedbackEntry(models.Model):
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE)
    course = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class PlacementQuestionSuggestion(models.Model):
    question = models.TextField()
    tags = models.CharField(max_length=255, blank=True, null=True)