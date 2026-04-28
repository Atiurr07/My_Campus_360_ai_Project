import streamlit as st
from Education.ai_service import parse_uploaded_file, analyze_resume_vs_jd
import time 


st.set_page_config(page_title="ATS Resume Analyzer", layout="wide")
st.title("ATS Resume Analyzer (Local + Gemini optional)")

with st.form("analyze"):
    uploaded = st.file_uploader("Upload Resume (pdf/docx/txt)", type=["pdf", "docx", "txt"])
    jd_text = st.text_area("Paste Job Description", height=250)
    target_role = st.text_input("Target role (optional)", help="e.g. data analyst")
    generate_suggestions = st.checkbox("Generate AI suggestions (slower)", value=True)
    submitted = st.form_submit_button("Analyze Resume")

if submitted:
    if not uploaded or not jd_text.strip():
        st.error("Please Upload a resume file and paste a job description.")
    else:
        # step-wise progress indicator
        progress = st.progress(0)
        status = st.empty(0)

        status.info("Parsing uploaded file...")
        progress.progress(10)

        # parse file::
        resume_text = parse_uploaded_file(uploaded)
        time.sleep(0.3)

        status.info("Extracting keywords...")
        progress.progress(30)
        time.sleep(0.2)

        status.info("Computing embeddings & matching....")
        progress.progress(55)

        # we call analyze_resume_vs_jd but with generate_suggestions False to keep stepwise control
        report  = analyze_resume_vs_jd(resume_text, jd_text, target_role or None, generate_suggestions=False)
        time.sleep(0.3)

        status.info("Generating suggestions (optional)....")
        if generate_suggestions:
            progress.progress(75)

            # run generation separatelly (this may be slow)
            sugg, opt_text = generate_suggestions(report.get("missing_keywords", []), report.get("sections", {}), jd_text, resume_text, target_role)

            # If generated_suggestions signature differs, fall back to ai_service.llm_generate usages
            report["suggestions"] = sugg
            report["optimized_resume_text"] = opt_text
            time.sleep(0.5)
        else:
            report["suggestions"] = []
            report["optimized_resume_text"] = ""

        progress.progress(100)
        status.success("Analysis complete.")

        # Display result
        st.header("Analysis Summary")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Final Match", f"{report.get('final_score', report.get('keyword_match_percent', 0))}%")
        c2.metric("Keyword Match", f"{report.get('keyword_match_percent', 0)}%")
        c3.metric("Semantic Sim", f"{report.get('semantic_similarity_percent', 0)}%")
        c4.metric("ATS Score", f"{report.get('ats_score', 0)}%")

        st.subheader("Missing Keywords")
        if report["missing_keywords"]:
            st.write(report.get("missing_keywords"))
        else:
            st.write("No missing keywords detected (based on JD)")
        
        st.subheader("Suggestions")
        for s in report.get("suggestions", []):
            st.markdown(f"-{s}")

        st.subheader("Optional Resume (preview)")
        st.text_area("Optomized Resume", value=report["optimized_resume_text"][:4000], height=300)

        st.download_button("Download Optimized Resume (text)", report.get("optimized_resume_text"), file_name="optimized_resume.txt")