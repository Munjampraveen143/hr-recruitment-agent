
import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from resume_parser import parse_resume
from agent import (
    screen_candidate,
    generate_interview_questions,
    generate_hr_email,
)
from database import (
    initialize_database,
    save_candidate,
    get_candidates,
    delete_candidate,
)
from matching import calculate_similarity


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="HR Recruitment AI Agent",
    page_icon="👥",
    layout="wide",
)

initialize_database()


# =====================================================
# SESSION STATE
# =====================================================

if "candidate" not in st.session_state:
    st.session_state.candidate = None

if "report" not in st.session_state:
    st.session_state.report = None

if "saved_candidate_id" not in st.session_state:
    st.session_state.saved_candidate_id = None


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def display_list(items):
    """Display a list of items safely."""

    if not items:
        st.info("No information available.")
        return

    if isinstance(items, str):
        items = [items]

    for item in items:
        st.markdown(f"- {item}")


def reset_screening():
    """Reset the current screening."""

    st.session_state.candidate = None
    st.session_state.report = None
    st.session_state.saved_candidate_id = None


def process_resume(uploaded_file, job_description, job_title):
    """Parse and analyze the uploaded resume."""

    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:

        temp_file.write(uploaded_file.getvalue())
        temp_path = temp_file.name

    try:

        candidate = parse_resume(temp_path)

        report = screen_candidate(
            candidate["resume_text"],
            job_description,
        )

        candidate["job_title"] = job_title
        candidate["job_description"] = job_description

        return candidate, report

    finally:

        Path(temp_path).unlink(
            missing_ok=True
        )


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("HR Recruitment Agent")

st.sidebar.caption(
    "Powered by Ollama + Llama 3.2"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Resume Screening",
        "Interview Questions",
        "HR Email Generator",
        "Candidate Database",
    ],
)

st.sidebar.divider()

st.sidebar.info(
    "AI-generated reports are advisory. "
    "Final recruitment decisions must be made "
    "by qualified human reviewers."
)


# =====================================================
# DASHBOARD
# =====================================================

if page == "Dashboard":

    st.title("HR Recruitment AI Agent")

    st.write(
        "AI-assisted recruitment workflow "
        "running locally using Ollama."
    )

    candidates = get_candidates()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Candidates",
        len(candidates),
    )

    col2.metric(
        "AI Model",
        "Llama 3.2",
    )

    col3.metric(
        "Database",
        "SQLite",
    )

    st.divider()

    st.subheader("Recruitment Workflow")

    st.markdown(
        """
        1. Upload a candidate resume.
        2. Enter the job description.
        3. Analyze job-related skills.
        4. Review the AI-generated report.
        5. Save the candidate.
        6. Generate interview questions.
        7. Draft HR communication.
        """
    )

    st.subheader("Available Modules")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            **Resume Screening**

            Extract candidate information and
            analyze job-related skills.
            """
        )

        st.markdown(
            """
            **Interview Questions**

            Generate questions based on the
            resume and job description.
            """
        )

    with col2:

        st.markdown(
            """
            **Candidate Database**

            Store and manage candidate records.
            """
        )

        st.markdown(
            """
            **HR Email Generator**

            Draft professional recruitment emails.
            """
        )


# =====================================================
# RESUME SCREENING
# =====================================================

elif page == "Resume Screening":

    st.title("Resume Screening")

    st.write(
        "Upload a resume and compare it against "
        "a job description."
    )

    col1, col2 = st.columns(2)

    with col1:

        job_title = st.text_input(
            "Job Title",
            placeholder="Junior Data Analyst",
        )

    with col2:

        uploaded_file = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"],
        )

    job_description = st.text_area(
        "Job Description",
        height=220,
        placeholder=(
            "Enter job responsibilities, "
            "required skills, qualifications, "
            "and experience..."
        ),
    )

    col1, col2 = st.columns(2)

    with col1:

        analyze_button = st.button(
            "Analyze Resume",
            type="primary",
            use_container_width=True,
        )

    with col2:

        reset_button = st.button(
            "Clear Screening",
            use_container_width=True,
        )

    if reset_button:

        reset_screening()
        st.rerun()

    if analyze_button:

        if not uploaded_file:

            st.error(
                "Please upload a resume."
            )

        elif not job_description.strip():

            st.error(
                "Please enter a job description."
            )

        elif not job_title.strip():

            st.error(
                "Please enter a job title."
            )

        else:

            try:

                with st.spinner(
                    "Extracting resume information "
                    "and analyzing with Ollama..."
                ):

                    candidate, report = process_resume(
                        uploaded_file,
                        job_description,
                        job_title,
                    )

                st.session_state.candidate = candidate
                st.session_state.report = report

                st.session_state.saved_candidate_id = None

            except Exception as error:

                st.error(
                    f"Resume processing failed: {error}"
                )

    # -------------------------------------------------
    # DISPLAY SCREENING RESULTS
    # -------------------------------------------------

    candidate = st.session_state.candidate
    report = st.session_state.report

    if candidate and report:

        if "error" in report:

            st.error(
                report["error"]
            )

            if report.get("raw_response"):

                st.text(
                    report["raw_response"]
                )

        else:

            st.divider()

            st.subheader(
                candidate.get(
                    "name",
                    "Unknown Candidate",
                )
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"Email: "
                    f"{candidate.get('email') or 'Not found'}"
                )

            with col2:

                st.write(
                    f"Phone: "
                    f"{candidate.get('phone') or 'Not found'}"
                )

            # Similarity indicator

            similarity = calculate_similarity(
                candidate["job_description"],
                candidate["resume_text"],
            )

            ai_score = report.get(
                "match_score",
                0,
            )

            st.subheader(
                "Screening Indicators"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "AI Match Indicator",
                    f"{ai_score}%",
                )

            with col2:

                st.metric(
                    "Text Similarity",
                    f"{similarity}%",
                )

            st.caption(
                "These scores are preliminary indicators "
                "and must not be used as automatic "
                "hiring or rejection decisions."
            )

            # Candidate summary

            st.subheader(
                "Candidate Summary"
            )

            st.write(
                report.get(
                    "summary",
                    "No summary available.",
                )
            )

            # Skills

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    "### Relevant Skills"
                )

                display_list(
                    report.get(
                        "relevant_skills",
                        [],
                    )
                )

                st.markdown(
                    "### Strengths"
                )

                display_list(
                    report.get(
                        "strengths",
                        [],
                    )
                )

            with col2:

                st.markdown(
                    "### Missing or Unclear Skills"
                )

                display_list(
                    report.get(
                        "missing_skills",
                        [],
                    )
                )

                st.markdown(
                    "### Areas to Verify"
                )

                display_list(
                    report.get(
                        "areas_to_verify",
                        [],
                    )
                )

            # Experience

            with st.expander(
                "Experience Evidence"
            ):

                display_list(
                    report.get(
                        "experience_evidence",
                        [],
                    )
                )

            # Education

            with st.expander(
                "Education Evidence"
            ):

                display_list(
                    report.get(
                        "education_evidence",
                        [],
                    )
                )

            # Save candidate

            st.divider()

            if st.session_state.saved_candidate_id:

                st.success(
                    "Candidate saved successfully. "
                    f"ID: "
                    f"{st.session_state.saved_candidate_id}"
                )

            else:

                if st.button(
                    "Save Candidate to Database",
                    type="primary",
                ):

                    try:

                        candidate_id = save_candidate(
                            candidate["name"],
                            candidate["email"],
                            candidate["phone"],
                            candidate["job_title"],
                            candidate["resume_text"],
                            report,
                        )

                        st.session_state.saved_candidate_id = (
                            candidate_id
                        )

                        st.success(
                            "Candidate saved successfully."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Database error: {error}"
                        )


# =====================================================
# INTERVIEW QUESTION GENERATOR
# =====================================================

elif page == "Interview Questions":

    st.title(
        "Interview Question Generator"
    )

    st.write(
        "Generate interview questions based on "
        "the candidate's resume and job requirements."
    )

    resume_text = st.text_area(
        "Candidate Resume",
        height=220,
        placeholder="Paste candidate resume text...",
    )

    job_description = st.text_area(
        "Job Description",
        height=220,
        placeholder="Paste job description...",
    )

    if st.button(
        "Generate Questions",
        type="primary",
    ):

        if not resume_text.strip():

            st.error(
                "Please enter candidate resume text."
            )

        elif not job_description.strip():

            st.error(
                "Please enter a job description."
            )

        else:

            with st.spinner(
                "Generating interview questions..."
            ):

                result = generate_interview_questions(
                    resume_text,
                    job_description,
                )

            if result.startswith("ERROR:"):

                st.error(result)

            else:

                st.subheader(
                    "Generated Interview Questions"
                )

                st.markdown(result)

                st.download_button(
                    "Download Questions",
                    data=result,
                    file_name="interview_questions.txt",
                    mime="text/plain",
                )


# =====================================================
# HR EMAIL GENERATOR
# =====================================================

elif page == "HR Email Generator":

    st.title(
        "HR Email Generator"
    )

    st.write(
        "Generate professional recruitment emails."
    )

    candidate_name = st.text_input(
        "Candidate Name",
        placeholder="Candidate name",
    )

    job_title = st.text_input(
        "Job Title",
        placeholder="Junior Data Analyst",
    )

    email_type = st.selectbox(
        "Email Type",
        [
            "Interview Invitation",
            "Interview Confirmation",
            "Interview Follow-up",
            "Request Additional Information",
            "Application Acknowledgement",
            "Application Status Update",
        ],
    )

    if st.button(
        "Generate Email",
        type="primary",
    ):

        if not candidate_name.strip():

            st.error(
                "Please enter candidate name."
            )

        elif not job_title.strip():

            st.error(
                "Please enter job title."
            )

        else:

            with st.spinner(
                "Generating HR email..."
            ):

                email = generate_hr_email(
                    candidate_name,
                    job_title,
                    email_type,
                )

            if email.startswith("ERROR:"):

                st.error(email)

            else:

                st.subheader(
                    "Generated Email"
                )

                st.text_area(
                    "Email Draft",
                    value=email,
                    height=300,
                )

                st.download_button(
                    "Download Email",
                    data=email,
                    file_name="hr_email.txt",
                    mime="text/plain",
                )


# =====================================================
# CANDIDATE DATABASE
# =====================================================

elif page == "Candidate Database":

    st.title(
        "Candidate Database"
    )

    candidates = get_candidates()

    if candidates:

        df = pd.DataFrame(
            candidates
        )

        # Remove report column from table

        display_df = df.drop(
            columns=[
                "screening_report",
            ],
            errors="ignore",
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.subheader(
            "View Candidate Report"
        )

        candidate_ids = [
            row["id"]
            for row in candidates
        ]

        selected_id = st.selectbox(
            "Select Candidate ID",
            candidate_ids,
        )

        selected_candidate = next(
            (
                row
                for row in candidates
                if row["id"] == selected_id
            ),
            None,
        )

        if selected_candidate:

            st.write(
                f"Candidate: "
                f"{selected_candidate['name']}"
            )

            st.write(
                f"Job Title: "
                f"{selected_candidate['job_title']}"
            )

            try:

                screening_report = json.loads(
                    selected_candidate[
                        "screening_report"
                    ]
                )

                st.json(
                    screening_report
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):

                st.warning(
                    "Could not load screening report."
                )

            st.divider()

            if st.button(
                "Delete Selected Candidate",
                type="secondary",
            ):

                delete_candidate(
                    selected_id
                )

                st.success(
                    "Candidate deleted successfully."
                )

                st.rerun()

        # CSV export

        csv_data = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Export Candidates to CSV",
            data=csv_data,
            file_name="candidates.csv",
            mime="text/csv",
        )

    else:

        st.info(
            "No candidates have been saved yet. "
            "Use Resume Screening to add candidates."
        )
