import requests
from django.conf import settings

BASE_URL = settings.HF_AI_BASE_URL
TIMEOUT = 300

# Resume Analyzer 
def analyze_resume_vs_jd(resume_text, jd_text, target_role=None):
    payload = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "target_role": target_role or "",
    }

    resp = requests.post(
        f"{BASE_URL}/resume/analyze",
        json=payload,
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()

# Study Plan
def generate_study_plan_from_syllabus(
        syllabus_text,
        weak_topics = None,
        hours_per_day=2,
        start_date = None,
        deadline = None,
        goals=None,
):
    payload = {
        "syllabus_text": syllabus_text,
        "weak_topics": weak_topics or [],
        "hours_per_day": hours_per_day,
        "start_date": start_date,
        "deadline": deadline,
        "goals": goals,
    }

    resp = requests.post(
        f"{BASE_URL}/study/plan",
        json=payload,
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()

# Doubt Solver::
def ai_doubt_solver(question, topics=None):
    payload = {
        "question": question,
        "topics": topics or [],
    } 
    resp = requests.post(
        f"{BASE_URL}/study/doubt",
        json=payload,
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()


# AI Assistant:;
def ai_assistant(query):
    try:
        resp = requests.post(
            f"{BASE_URL}/ai/assistant",
            json={"query": query},
            timeout=30
        )

        print("HF Status  Code:", resp.status_code)
        print("HF Raw Response:", resp.text)

        if resp.status_code != 200:
            return {"error": f"HF error: {resp.status_code}"}
        return resp.json()
    except requests.exceptions.ReadTimeout:
        return {"error": "Timeout: HF took too long to response."}
    except requests.exceptions.ConnectionError:
        return {"error": "COnnection failed to Hugging face."}
    
    except Exception as e:
        return {"error": str(e)}