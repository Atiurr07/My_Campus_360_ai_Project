from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MeetingUploadForm, NoteForm
from .models import Meeting, Note, SentimentRecord
from .ai_service import summarize_transcript, analyze_sentiment
from django.contrib import messages


# Create your views here.
# 1. views for Meeting Uploading
@login_required
def meeting_upload(request):
    if request.method == "POST":
        form = MeetingUploadForm(request.POST)
        if form.is_valid():
            m= form.save(commit=False)
            m.user = request.user
            m.summary = summarize_transcript(m.transcript or "")
            m.save()
            messages.success(request, "Meeting saved and summarized.")
            return redirect("productivity:meeting_detail", m.id)
    else:
        form = MeetingUploadForm()
    return render(request, "productivity/meeting_upload.html", {"form": form})

# 2. views for Meeting details
@login_required
def meeting_detail(request, pk):
    m= Meeting.objects.get(pk=pk, user=request.user)
    return render(request, "productivity/meeting_detail.html", {"m": m})

# 3. views for Note Creation::
@login_required
def notes_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            n = form.save(commit=False)
            n.user = request.user
            n.save()
            messages.success(request, "NOte saved")
            return redirect("productivity:notes_list")
    else:
        form = NoteForm()
    return render(request, "productivity/note_create.html", {"form":form})

# 4. views  for notes list:
@login_required
def notes_list(request):
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "productivity/notes_list.html", {"notes": notes})

# 5. views for sentiment_analysis::
@login_required
def sentiment_analyze(request):
    result = None
    if request.method == "POST":
        text = request.POST.get("text")
        sentiment = analyze_sentiment(text)
        SentimentRecord.objects.create(uset=request.user, text=text, sentiment=sentiment)
        result = sentiment
    return render(request, "productivity/sentiment.html", {"result": result})