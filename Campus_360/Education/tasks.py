from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.urls import reverse
from .models import Resume, StudyPlanRequest, StudyPlan, StudyPlanItem, SyllabusUpload, TopicDifficulty

from services.ai_gateway import generate_study_plan_from_syllabus, analyze_resume_vs_jd
from .utils import extract_text_from_file, flatten_ai_plan_to_items, parse_uploaded_file 

from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from django.conf import settings

## This is for ** Resume Section ** 

logger = get_task_logger(__name__)

def _cache_progress(task_id, status, progress, message, extra=None):
    payload = {"status": status, "progress": progress, "message": message}
    if extra:
        payload.update(extra)
    cache.set(f"resume_task_{task_id}", payload, timeout=60 * 60)

@shared_task(bind=True)
def analyze_resume_task(self, resume_id, jd_text, target_role, user_id, generate_suggestions=True):
    task_id = self.request.id
    _cache_progress(task_id, "started", 5, "Task started")

    try:
        resume = Resume.objects.get(pk=resume_id)
    except Resume.DoesNotExist:
        _cache_progress(task_id, "error", 100, "Resume not found")
        self.update_state(state="FAILURE", meta={"error": "Resume not found"})
        return {"error": "Resume not found"}

    try:
        _cache_progress(task_id, "parsing", 20, "Parsing uploaded file")
        parsed_text = parse_uploaded_file(resume.uploaded_file)
        resume.parsed_text = parsed_text
        resume.save(update_fields=["parsed_text"])

        _cache_progress(task_id, "analyzing", 50, "Analyzing resume vs job description")
        report = analyze_resume_vs_jd(parsed_text, jd_text or "", target_role or None)

        _cache_progress(task_id, "saving", 85, "Saving results")
        resume.feedback = report
        resume.ats_score = report.get("ats_score", 0.0)
        resume.keyword_match_score = report.get("keyword_match_percent", 0.0)
        resume.save(update_fields=["feedback", "ats_score", "keyword_match_score", "updated_at"])

        _cache_progress(task_id, "done", 100, "Analysis complete", {"redirect_url": reverse("education:resume_detail", args=[resume.pk])})
        self.update_state(state="SUCCESS", meta={"result": report})
        return report

    except Exception as e:
        import traceback
        logger.exception("Task failed")
        _cache_progress(task_id, "error", 100, f"Error: {str(e)}")
        raise ValueError(f"Task failed: {str(e)}\n{traceback.format_exc()}")

# ====================================================
# This is for ** AI_studuy Plan Generator **

@shared_task(bind=True)
def generate_study_plan_task(self, request_id):
    from django.db import transaction
    import traceback, re, os

    print("Task Started, request_id = ", request_id)

    req = StudyPlanRequest.objects.get(id=request_id)
    req.status = "running"
    req.save(update_fields=["status"])

    ai_json = None  # ✅ ensure it's always defined

    try:
        raw_text = ""
        # --- Step 1: Extract syllabus text safely ---
        if req.syllabus and getattr(req.syllabus, "syllabus_file", None):
            syllabus_file = req.syllabus.syllabus_file
            print("Syllabus file:", syllabus_file)

            # Make sure the file path has a valid path
            if hasattr(syllabus_file, "path") and os.path.exists(syllabus_file.path):
                file_path = syllabus_file.path
                raw_text = extract_text_from_file(file_path)
            else:
                raise FileNotFoundError(f"Invalid or missing file path for syllabus: {syllabus_file}")
        else:
            print("🧩 DEBUG:", file_path, type(file_path))
            raw_text = req.params.get("syllabus_text", "")
            print("Extracted text length:", len(raw_text))
            if not raw_text:
                raise ValueError("No valid syllabus file or syllabus text provided.")

        # --- Step 2: Prepare parameters ---
        weak_topics = req.params.get("weak_topics", []) or []
        hours_per_day = int(req.params.get("hours_per_day", 2))
        start_date = req.params.get("start_date")
        deadline = req.params.get("deadline")
        goals = req.params.get("goals", "")

        # --- Step 3: Generate Study Plan from AI ---
        try:
            ai_json = generate_study_plan_from_syllabus(
                syllabus_text=raw_text,
                weak_topics=weak_topics,
                hours_per_day=hours_per_day,
                start_date=start_date,
                deadline=deadline,
                goals=goals,
            )
            print(" AI Response keys:", ai_json.keys())
            print(" Days count:", len(ai_json.get("days", [])))
        except re.error as re_err:
            req.status = "failed"
            req.result_summary = f"Regex error: {re_err}"
            req.save()
            print("🔴 REGEX ERROR:", re_err)
            print(traceback.format_exc())
            return

        if not ai_json:
            req.status = "failed"
            req.result_summary = "AI generation returned empty or invalid data."
            req.save()
            return

        # --- Step 4: Save AI response safely ---
        req.result_json = ai_json
        req.result_summary = ai_json.get("summary", "")
        req.status = "done"
        req.save()

        # --- Step 5: Persist plan ---
        with transaction.atomic():
            days = ai_json.get("days", [])

            # deactivate older plans
            StudyPlan.objects.filter(
                user=req.user,
                active=True
            ).update(active=False)

            plan = StudyPlan.objects.create(
                request=req,
                user=req.user,
                meta={
                    "total_days": ai_json.get("total_days", len(days)
                    ),
                    "days": days,
                    "goals": goals,
                },
            )

            print("Study created, id = ", plan.id)
            start_date = req.params.get("start_date")
            items = flatten_ai_plan_to_items(ai_json, start_date)
            print(" Items to save:", len(items))
            for idx, it in enumerate(items, start=1):
                StudyPlanItem.objects.create(
                    plan=plan,
                    date=it["date"],
                    topic=it["topic"],
                    duration_minutes=it["hours"] * 60,
                    notes=it["tasks"],
                    difficulty_score=ai_json.get("difficulty_map", {}).get(it["topic"]),
                )

            for topic, diff in ai_json.get("difficulty_map", {}).items():
                TopicDifficulty.objects.update_or_create(
                    user=req.user,
                    topic=topic,
                    defaults={"difficulty": diff},
                )
                print("Task completed successfully.")
                print("FULL AI RESPONSE:", ai_json)
    except Exception as e:
        try:
            req.status = "failed"
            req.result_summary = f"Error: {e}\n\n{traceback.format_exc()}"
            req.save()
            print("❌ Task Failed:", traceback.format_exc())
        except Exception:
            pass
        return

@shared_task
def adapt_study_plan_weekly():
    """
    Celery beat task: runs weekly to adapt existing study plans.
    Uses completion data to identify weak topics and regenerate plan.
    """

    now = timezone.now()

    for plan in StudyPlan.objects.filter(active=True):
        week_start = now.date()
        week_end = week_start + datetime.timedelta(days=7)
        items = plan.items.filter(date_range=(week_start, week_end))

        completed = items.filter(complex=True).count()
        total = items.count() or 1
        completion_rate = completed / total

        # if low completion rate, trigger adaptive replan
        if completion_rate < 0.6:
            req = plan.request
            weak_topics = list(
                plan.items.filter(completed=False)
                .values_list("topic", flat=True)
                .distinct()
            )

            req.params["weak_topics"] = weak_topics
            req.save()
            generate_study_plan_task.delay(req.id)