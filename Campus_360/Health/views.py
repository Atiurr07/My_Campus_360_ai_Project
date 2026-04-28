from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ChatForm, SymptomForm, SleepForm
from .ai_service import mental_health_response, symptom_checker
from .models import ChatLog, SymptomLog, SleepLog
from django.contrib import messages


# Create your views here.

# 1. view for chat option::
def chat(request):
    if request.method == "POST":
        form = ChatForm(request.POST)
        if form.is_valid():
            msg = form.cleaned_data['message']
            resp = mental_health_response(msg)
            log = ChatLog.objects.create(user=request.user, user_message=msg, bot_response = resp)
            return render(request, "health/chat.html", {"form": ChatForm(), "resp": resp, "log": log})
    else:
        form = ChatForm()
    return render(request, "health/chat.html", {"form": form})


# 2. view for symptom check::
@login_required
def symptom_check(request):
    s= None
    if request.method == "POST":
        form = SymptomForm(request.POST)
        if form.is_valid():
            s = form.save(commit = False)
            s.user = request.user
            s.result = symptom_checker(s.symptom_text)
            s.save()
            messages.success(request, "Symptomm check compleated.")
            return redirect("health:symptom_result", s.id)
    else:
        form = SymptomForm()
        return render(request, "health/symptom_result.html", {"s":s})


# 3. view for symptom result
@login_required
def symptom_result(request, pk):
    s = SymptomLog.objects.get(pk=pk, user=request.user)
    return render(request, "health/symptom_result.html", {"s": s})


# 4. view for sleep Log symptom
def sleep_log(request):
    if request.method == "POST":
        form = SleepForm(request.POST)
        if form.is_valid():
            s1 = form.save(commit=False)
            s1.user = request.user

            # simple quality heuristics 
            s1.quality = "Good" if s1.sleep_hours >= 7 else "Poor"
            s1.save()
            messages.success(request, "Sleep log saved.")
            return redirect("health:sleep_log")
    else:
        form = SleepForm()
    logs = SleepLog.objects.filter(user=request.user).order_by('-date')[:10]
    return render(request, "health/sleep_log.html", {"form": form, "logs": logs})
