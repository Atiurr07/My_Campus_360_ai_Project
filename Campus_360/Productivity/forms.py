from django import forms
from .models import Meeting, Note

class MeetingUploadForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'transcript']
    

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields  = ['title', 'content', 'tags']