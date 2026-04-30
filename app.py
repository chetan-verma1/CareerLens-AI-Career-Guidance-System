from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import pandas as pd
import os
import uuid

INDIA_STATES_AND_UTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
    "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry"
]

from modules.career_pipeline import run_pipeline
from modules.resume_analyzer import analyze_resume
from modules.career_model import predict_career
from modules.career_skill import skill_gap_analysis
from modules.salary_prediction import predict_salary
from modules.resume_ats import general_ats_score, role_specific_ats_score, ats_verdict
from modules.skill_db import skill_database

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FOLDER = os.path.join(BASE_DIR, "data")

ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_UPLOAD_SIZE_MB = 5

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================
# FILE UPLOAD SECURITY HELPERS
# ==============================
def allowed_file(filename: str) -> bool:
    """Check whether uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_uploaded_resume(file):
    """
    Validate and save uploaded resume with a unique secure filename.
    Returns the saved file path.
    """
    if not file or file.filename == "":
        raise ValueError("Please upload a valid resume file.")

    if not allowed_file(file.filename):
        raise ValueError("Only PDF and DOCX resume files are allowed.")

    original_filename = secure_filename(file.filename)

    if not original_filename:
        raise ValueError("Invalid file name.")

    extension = original_filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

    file.save(filepath)
    return filepath


def cleanup_uploaded_file(filepath: str):
    """Delete uploaded resume after processing."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Could not delete uploaded file {filepath}: {e}")


def validate_resume_document(filepath: str):
    """
    Validate whether uploaded PDF/DOCX appears to be a resume.
    This prevents random PDFs/DOCX files from being processed.
    """
    resume_data = analyze_resume(filepath)

    if not resume_data:
        raise ValueError("Uploaded file could not be analyzed as a resume.")

    raw_text = str(resume_data.get("Raw_Text", "")).strip()
    skills = resume_data.get("Skills", []) or []
    education = resume_data.get("Education", []) or []
    experience = resume_data.get("Experience (Years)", 0)

    if len(raw_text) < 100:
        raise ValueError("Uploaded file does not contain enough resume content.")

    text_lower = raw_text.lower()

    resume_keywords = [
        "resume", "curriculum vitae", "cv",
        "education", "qualification", "academic",
        "experience", "work experience", "internship",
        "skills", "technical skills", "projects",
        "certification", "objective", "profile",
        "summary", "contact", "email", "phone"
    ]

    keyword_matches = sum(1 for keyword in resume_keywords if keyword in text_lower)

    has_email_or_phone = (
        "@" in raw_text
        or any(char.isdigit() for char in raw_text)
    )

    has_resume_signals = (
        len(skills) >= 1
        or len(education) >= 1
        or float(experience or 0) > 0
        or keyword_matches >= 2
    )

    if not has_resume_signals or not has_email_or_phone:
        raise ValueError(
            "This file does not appear to be a resume. Please upload a valid resume PDF or DOCX file."
        )

    return resume_data


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    message = f"File is too large. Maximum allowed size is {MAX_UPLOAD_SIZE_MB} MB."

    if request.path.startswith("/ats_resume_check"):
        return jsonify({"error": message}), 413

    return render_template(
        "index.html",
        result=None,
        resume_result=None,
        error=message,
        active_section="upload"
    ), 413


def _safe_read_csv(path: str):
    try:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df.columns = [str(c).strip() for c in df.columns]
            return df
    except Exception as e:
        print(f"Could not read {path}: {e}")
    return None


def load_dynamic_options():
    jobs_path = os.path.join(DATA_FOLDER, "jobs.csv")
    career_skills_path = os.path.join(DATA_FOLDER, "career_skills.csv")
    salary_path = os.path.join(DATA_FOLDER, "salary_data.csv")
    career_profiles_path = os.path.join(DATA_FOLDER, "career_role_profiles.csv")

    roles = set()
    domains = set()
    states = set()
    skills = set(str(v).strip() for v in skill_database if str(v).strip())

    def format_option(value):
        value = str(value).strip()
        if not value:
            return ""

        special_words = {
            "ai": "AI",
            "ml": "ML",
            "ui": "UI",
            "ux": "UX",
            "hr": "HR",
            "qa": "QA",
            "seo": "SEO",
            "sql": "SQL",
            "api": "API",
            "aws": "AWS",
            "iot": "IoT",
            "devops": "DevOps",
            "nlp": "NLP",
            "ocr": "OCR",
            "ats": "ATS",
            "mca": "MCA",
            "bca": "BCA",
            "cse": "CSE",
            "it": "IT",
        }

        words = value.replace("_", " ").replace("-", " ").split()
        formatted_words = []

        for word in words:
            key = word.lower()
            formatted_words.append(special_words.get(key, word.capitalize()))

        return " ".join(formatted_words)

    def unique_formatted_options(values):
        seen = {}

        for value in values:
            formatted = format_option(value)
            if not formatted:
                continue

            key = formatted.lower()
            if key not in seen:
                seen[key] = formatted

        return sorted(seen.values())

    for path in [jobs_path, career_skills_path, salary_path, career_profiles_path]:
        df = _safe_read_csv(path)
        if df is None:
            continue

        for role_col in [
            "Role",
            "role",
            "Career",
            "career",
            "Career Role",
            "career_role",
            "Job Role",
            "job_role",
            "Job Title",
            "job_title",
            "Title",
            "title",
        ]:
            if role_col in df.columns:
                roles.update(
                    str(v).strip()
                    for v in df[role_col].dropna().tolist()
                    if str(v).strip()
                )

        for domain_col in [
            "Domain",
            "domain",
            "Career Domain",
            "career_domain",
            "Job Domain",
            "job_domain",
        ]:
            if domain_col in df.columns:
                domains.update(
                    str(v).strip()
                    for v in df[domain_col].dropna().tolist()
                    if str(v).strip()
                )

        for state_col in ["State", "state", "Location", "location"]:
            if state_col in df.columns:
                states.update(
                    str(v).strip()
                    for v in df[state_col].dropna().tolist()
                    if str(v).strip()
                )

    if not states:
        states.update(INDIA_STATES_AND_UTS)

    return {
        "roles": unique_formatted_options(roles),
        "domains": unique_formatted_options(domains),
        "states": sorted(states),
        "skills": sorted(skills),
    }

# ==============================
# LANDING PAGE
# ==============================
@app.route("/")
def landing():
    return render_template("landing.html")


# ==============================
# EXPLORE PAGE
# ==============================
@app.route("/explore")
def explore():
    return render_template("explore.html")


# ==============================
# MAIN APP PAGE
# ==============================
@app.route("/app", methods=["GET", "POST"])
def index():
    result = None
    resume_result = None
    error = None
    active_section = "upload"

    if request.method == "POST":
        tool_type = request.form.get("tool_type", "smart_analyzer")
        file = request.files.get("resume")
        filepath = None

        try:
            filepath = save_uploaded_resume(file)
            validated_resume_data = validate_resume_document(filepath)

            if tool_type == "resume_analyzer":
                resume_result = validated_resume_data
                active_section = "resumeTool"

                if not resume_result or not resume_result.get("Raw_Text"):
                    error = "Could not extract details from this resume."
                    resume_result = None

            else:
                result = run_pipeline(filepath)
                active_section = "upload"

                if not result:
                    error = "Could not extract data from this resume. Try another file."
                    return render_template(
                        "index.html",
                        result=None,
                        resume_result=None,
                        error=error,
                        active_section="upload"
                    )

                if "top3" not in result or not result["top3"]:
                    error = "Prediction failed. Resume content may be insufficient."
                    return render_template(
                        "index.html",
                        result=None,
                        resume_result=None,
                        error=error,
                        active_section="upload"
                    )

                labels = []
                values = []

                for career, conf in result["top3"]:
                    labels.append(career)
                    values.append(float(conf))

                result["labels"] = labels
                result["values"] = values

        except ValueError as e:
            error = str(e)

        except Exception as e:
            print("\n🚨 ERROR OCCURRED:")
            print(str(e))
            error = "Error processing resume. Please upload a proper PDF/DOCX file."

        finally:
            cleanup_uploaded_file(filepath)

    return render_template(
        "index.html",
        result=result,
        resume_result=resume_result,
        error=error,
        active_section=active_section
    )


# ==============================
# META OPTIONS API
# ==============================
@app.route("/meta/options", methods=["GET"])
def meta_options():
    try:
        return jsonify(load_dynamic_options())
    except Exception as e:
        print("\n🚨 META OPTIONS ERROR:")
        print(str(e))
        return jsonify({
            "roles": [],
            "domains": [],
            "states": [],
            "skills": []
        }), 200


# ==============================
# CAREER PREDICTOR API
# ==============================
@app.route("/career_model", methods=["POST"])
def career_model_api():
    data = request.get_json() or {}

    text = str(data.get("text", "")).strip()
    skills = data.get("skills", [])
    education = data.get("education", "")
    experience = data.get("experience", data.get("experience_years", 0))
    domain = str(data.get("domain", "")).strip()

    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    if not isinstance(skills, list):
        skills = []

    skills = [str(skill).strip() for skill in skills if str(skill).strip()]

    if not text and not skills:
        return jsonify({
            "error": "Please enter resume text or at least one skill for career prediction."
        }), 400

    try:
        experience = float(experience)
        if experience < 0:
            experience = 0
    except (TypeError, ValueError):
        experience = 0

    payload = {
        "text": text,
        "skills": skills,
        "education": [education] if isinstance(education, str) and education.strip() else education,
        "experience_years": experience,
        "domain": domain,
    }

    bundle = predict_career(payload, top_k=3, return_details=True)
    top3 = bundle.get("top3", [])
    predictions = bundle.get("predictions", [])
    inferred_domain = bundle.get("inferred_domain", "")

    if not top3:
        return jsonify({
            "error": "Unable to generate career recommendations from the provided input."
        }), 400

    top_domains = []
    for item in predictions[:3]:
        item_domain = str(item.get("domain") or "").strip()
        if item_domain and item_domain not in top_domains:
            top_domains.append(item_domain)

    return jsonify({
        "top3_roles": top3,
        "predicted_domain": inferred_domain or (top_domains[0] if top_domains else ""),
        "secondary_domain": top_domains[1] if len(top_domains) > 1 else "",
        "is_hybrid_profile": len(top_domains) > 1 and top_domains[0] != top_domains[1],
        "details": predictions,
    })

# ==============================
# SKILL GAP API
# ==============================
@app.route("/career_skill", methods=["POST"])
def career_skill_api():
    data = request.get_json() or {}

    career = str(data.get("career", "")).strip()
    skills = data.get("skills", [])

    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    if not isinstance(skills, list):
        skills = []

    skills = [str(skill).strip() for skill in skills if str(skill).strip()]

    if not career:
        return jsonify({
            "error": "Please select or enter a target career."
        }), 400

    if not skills:
        return jsonify({
            "error": "Please enter at least one skill for skill gap analysis."
        }), 400

    matched, missing, score = skill_gap_analysis(skills, career)

    return jsonify({
        "matched_skills": matched,
        "missing_skills": missing,
        "readiness_score": score
    })

# ==============================
# SALARY API
# ==============================
@app.route("/salary_prediction", methods=["POST"])
def salary_api():
    data = request.get_json() or {}

    role = str(data.get("role", "")).strip()
    domain = str(data.get("domain", "")).strip()
    state = str(data.get("state", "")).strip()

    if not role:
        return jsonify({
            "error": "Please select or enter a job role."
        }), 400

    if not domain:
        return jsonify({
            "error": "Please select a domain."
        }), 400

    if not state:
        return jsonify({
            "error": "Please select a state."
        }), 400

    try:
        exp = float(data.get("experience", 0))
        if exp < 0:
            return jsonify({
                "error": "Experience cannot be negative."
            }), 400
    except (TypeError, ValueError):
        return jsonify({
            "error": "Experience must be a valid number."
        }), 400

    salary_result = predict_salary(
        role=role,
        experience_years=exp,
        domain=domain,
        state=state
    )

    return jsonify({
        "salary_details": salary_result
    })

# ==============================
# ATS RESUME CHECK API
# ==============================
@app.route("/ats_resume_check", methods=["POST"])
def ats_resume_check():
    file = request.files.get("resume")
    role = request.form.get("role", "").strip()
    filepath = None

    if not role:
        return jsonify({"error": "Please enter a target role."}), 400

    try:
        filepath = save_uploaded_resume(file)

        resume_data = validate_resume_document(filepath)

        if not resume_data or not resume_data.get("Raw_Text"):
            return jsonify({"error": "Could not extract data from this resume."}), 400

        raw_text = resume_data.get("Raw_Text", "")
        extracted_skills = resume_data.get("Skills", [])
        experience = resume_data.get("Experience (Years)", 0)

        general_score, general_feedback = general_ats_score(
            raw_text,
            extracted_skills=extracted_skills,
            experience=experience
        )

        role_score, role_feedback = role_specific_ats_score(
            raw_text,
            role
        )

        verdict = ats_verdict(general_score, role_score)

        return jsonify({
            "general_ats": general_score,
            "role_ats": role_score,
            "general_ats_feedback": general_feedback,
            "role_ats_feedback": role_feedback,
            "verdict": verdict
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        print("\n🚨 ATS ERROR:")
        print(str(e))
        return jsonify({"error": "Error checking ATS score."}), 500

    finally:
        cleanup_uploaded_file(filepath)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")