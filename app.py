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

    roles = set()
    domains = set()
    states = set()
    skills = set(str(v).strip() for v in skill_database if str(v).strip())

    for path in [jobs_path, career_skills_path, salary_path]:
        df = _safe_read_csv(path)
        if df is None:
            continue

        if "Role" in df.columns:
            roles.update(
                str(v).strip() for v in df["Role"].dropna().tolist()
                if str(v).strip()
            )

        if "Domain" in df.columns:
            domains.update(
                str(v).strip() for v in df["Domain"].dropna().tolist()
                if str(v).strip()
            )

        if "State" in df.columns:
            states.update(
                str(v).strip() for v in df["State"].dropna().tolist()
                if str(v).strip()
            )

    if not states:
        states.update(INDIA_STATES_AND_UTS)

    return {
        "roles": sorted(roles),
        "domains": sorted(domains),
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

            if tool_type == "resume_analyzer":
                resume_result = analyze_resume(filepath)
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
    payload = {
        "text": data.get("text", ""),
        "skills": data.get("skills", []),
        "education": [data.get("education", "")] if isinstance(data.get("education", ""), str) else data.get("education", []),
        "experience_years": data.get("experience", data.get("experience_years", 0)),
        "domain": data.get("domain", ""),
    }

    bundle = predict_career(payload, top_k=3, return_details=True)
    top3 = bundle.get("top3", [])
    predictions = bundle.get("predictions", [])
    inferred_domain = bundle.get("inferred_domain", "")

    top_domains = []
    for item in predictions[:3]:
        domain = str(item.get("domain") or "").strip()
        if domain and domain not in top_domains:
            top_domains.append(domain)

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

    matched, missing, score = skill_gap_analysis(
        data.get("skills", []),
        data.get("career", "")
    )

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

    role = data.get("role", "").strip()
    domain = data.get("domain", "").strip()
    state = data.get("state", "").strip()

    try:
        exp = int(float(data.get("experience", 0)))
    except (TypeError, ValueError):
        exp = 0

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

        resume_data = analyze_resume(filepath)

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