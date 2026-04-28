from django import forms
from .models import Course, AttendanceRecord, FeedbackEntry, Service
from  Users.models import MainUser

class QueueRequestForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.filter(active=True))
    priority = forms.BooleanField(required=False, help_text = 'Priority (staff/disabled)')

class CancleTokenForm(forms.Form):
    confirm = forms.BooleanField(label="Confirm cancellation")



class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'course', 'date', 'period', 'status']

        def __init__(self, *args, **kwargs):
            teacher = kwargs.pop('teacher', None)
            super().__init__(*args, **kwargs)
            if teacher:
                self.fields['course'].queryset = Course.objects.filter(teacher=teacher)

class EnrollmentForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), label="Select Course")
    student = forms.ModelMultipleChoiceField(
        queryset=MainUser.objects.filter(role="student"),
        widget = forms.CheckboxSelectMultiple,
        label = "Select Students"
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher and teacher.role == "teacher":
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)
        else:
            # admin can see all courses
            self.fields['course'].queryset = Course.objects.all()

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedbackEntry
        fields = ['course', 'text']
