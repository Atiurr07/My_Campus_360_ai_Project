from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
MainUser = settings.AUTH_USER_MODEL


class Resume(models.Model):
    user = models.ForeignKey(MainUser,on_delete=models.CASCADE, related_name='resumes' )
    uploaded_file = models.FileField(upload_to='resumes/originals/')
    parsed_text = models.TextField(blank=True, null=True)
    feedback = models.JSONField(blank=True, null=True)
    ats_score = models.FloatField(default=0.0)
    keyword_match_score = models.FloatField(default=0.0)
    optimized_resume_file = models.FileField(upload_to='resume/optimized/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{ self.user.username} - Resume #{self.pk} ({self.created_at.date()})"


class Assignment(models.Model):
    teacher = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255, default="Assignment")
    description = models.TextField(blank=True, null=True)
    file= models.FileField(upload_to="assignments/", blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True) # year-month-date(yyyy-mm-dd)

    # for Samrt tracking fields
    total_students = models.PositiveIntegerField(default=0)
    submitted_count = models.PositiveBigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} by {self.teacher.username}"
    
    @property
    def is_overdue(self):
        if self.deadline:
            return timezone.now() > self.deadline
        return False
    
    @property
    def is_due_soon(self):
        if self.deadline:
            delta = self.deadline - timezone.now()
            # due within 48 hours
            return delta.total_seconds() > 0 and delta.days < 2
        return False
    
    def submission_percentage(self):
        if self.total_students == 0:
            return 0
        return int((self.submitted_count / self.total_students) * 100)

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name='submissions')
    submitted_file = models.FileField(upload_to="submissions/")
    note = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Grading
    grade = models.CharField(max_length=20, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    attempt = models.PositiveIntegerField(default=1)  # versioning support
    status = models.CharField(
        max_length=20,
        choices=[('Pending', 'pending'),
                ('Submitted', 'submitted'),
                ('Re-submitted', 're-submitted'),
                ('Completed', 'completed')],
        default="Pending")  # Submitted / Late / Graded

    class Meta:
        ordering = ("-submitted_at",)
        unique_together = (("assignment", "student", "attempt"),)

    def __str__(self):
        return f"{self.assignment.title} - {self.student} (Attempt {self.attempt})"



class PlagiarismReport(models.Model):
    score = models.FloatField(default=0.0)
    details = models.JSONField(blank=True, null= True)
    created_at = models.DateTimeField(auto_now_add=True)


#  ** Study Plan Model Section ** ::

class SyllabusUpload(models.Model):
    user = models.ForeignKey(MainUser, on_delete= models.CASCADE, related_name="syllabus_uploads")
    syllabus_file = models.FileField(upload_to="syllabus/")
    performance_file = models.FileField(upload_to="performance/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed = models.BooleanField(default=False)
    parsed_data = models.JSONField(blank=True, null=True) # this is used to store the extracted topics, list, etc.

    def __str__(self):
        return f"Syllabus {self.id} by {self.user.username}"

class StudyPlanRequest(models.Model):
    """ A user request to generate a studey plan. """
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name="study_requests")
    syllabus = models.ForeignKey(SyllabusUpload, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default="pending")
    params = models.JSONField(default=dict) #preferences (available_hours, start_date, deadline, goals)
    result_summary = models.TextField(blank=True, null=True)
    result_json = models.JSONField(null=True, blank=True) # final generated plan structured 
    last_updated = models.DateTimeField(auto_now=True)

class StudyPlan(models.Model):
    """ The active study plan persisted for a user."""
    request = models.OneToOneField(StudyPlanRequest, on_delete=models.CASCADE, related_name="plan")
    user = models.ForeignKey(MainUser, on_delete=models.CASCADE, related_name="study_plans")
    name = models.CharField(max_length=255, default="Personalized Study Plan")
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    meta = models.JSONField(null=True, blank=True)

    @property
    def duration_days(self):
        if not self.meta:
            return 0
        
        if "duration_days" in self.meta:
            return int(self.meta["duration_days"])

        if "days" in self.meta:
            return len(self.meta.get("days", []))
        
        return self.items.count()

class StudyPlanItem(models.Model):
    """ Day-by-day items of the study plan."""
    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name="items")
    date = models.DateField()
    topic = models.CharField(max_length=400)
    duration_minutes = models.PositiveIntegerField(default=60)
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    difficulty_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        ordering = ["date"]

class TopicDifficulty(models.Model):
    """ Stores difficulty score per topic (That can be reused for personalization)."""
    user = models.ForeignKey(MainUser, on_delete= models.CASCADE, related_name="topic_difficulties")
    topic = models.CharField(max_length=400)
    difficulty= models.FloatField()
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "topic")