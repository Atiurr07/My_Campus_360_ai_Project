from django import forms
from .models import SymptomLog, SleepLog

class ChatForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label="How are you feeling?")


class SymptomForm(forms.Form):
    class Meta:
        model = SymptomLog
        fields = ['symptoms_text']

class SleepForm(forms.ModelForm):
    class Meta:
        model = SymptomLog
        fields = ['symptoms_text']

class SleepForm(forms.ModelForm):
    class Meta:
        model = SleepLog
        fields = ["sleep_hours"]