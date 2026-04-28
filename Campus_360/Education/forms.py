from django import forms
from .models import Resume, Assignment, Submission, SyllabusUpload, StudyPlanRequest

class ResumeUploadForm(forms.ModelForm):
    target_role = forms.CharField(required=False, help_text="optional: Target role to optimize for, e.g. 'data analyst'")
    class Meta:
        model = Resume
        fields = ['uploaded_file']

class AssignmentUploadForm(forms.ModelForm):
    deadline = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"types": "datetime-local"}))

    class Meta:
        model = Assignment
        fields = ['title', 'description','file', 'deadline']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter assignment title'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe assignment'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class']= 'form-control'

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["submitted_file", "note"]
        widgets = {
            "submitted_file": forms.ClearableFileInput(attrs={'class': 'form-control'}),
            "note": forms.Textarea(attrs={'class': 'form-control', "rows": 2, "placeholder": "Optional note for teacher"})
        }


#  ** forms for Study Plan Generation ** 
class SyllabusUpladForm(forms.ModelForm):
    class Meta:
        model = SyllabusUpload
        fields = ["syllabus_file", "performance_file"]

class StudyPlanRequestForm(forms.ModelForm):
    #  includes parameters: hours_per_day, start_date, end_date, goals
    hours_per_day = forms.IntegerField(min_value=1, max_value=24, initial=2)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    goals = forms.CharField(required=False, widget=forms.Textarea, help_text="e.g., 'pass board exams, focus on algebra'")

    class Meta:
        model = StudyPlanRequest
        fields = []