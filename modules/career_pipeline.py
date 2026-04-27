from __future__ import annotations

from .resume_analyzer import analyze_resume
from .career_model import predict_career, _normalize_role_name
from .career_skill import skill_gap_analysis
from .salary_prediction import predict_salary
from .resume_ats import general_ats_score, role_specific_ats_score, ats_verdict


def run_pipeline(file_path):
    resume_data = analyze_resume(file_path)
    if not resume_data or not resume_data.get("Raw_Text"):
        return None

    prediction_payload = {
        "text": resume_data.get("Raw_Text", ""),
        "skills": resume_data.get("Skills", []),
        "education": resume_data.get("Education", []),
        "experience_years": resume_data.get("Experience (Years)", 0),
    }

    prediction_bundle = predict_career(prediction_payload, top_k=3, return_details=True)
    top3 = prediction_bundle.get("top3", [])
    predictions = prediction_bundle.get("predictions", [])
    if not top3:
        return None

    best_career, confidence = top3[0]
    best_career = _normalize_role_name(best_career)

    raw_text = resume_data.get("Raw_Text", "")
    general_score, general_feedback = general_ats_score(resume_data, raw_text)
    ats_breakdown = general_feedback.get("breakdown", {})
    verdict = ats_verdict(general_score)

    career_data = {}
    for item in predictions:
        career = item["role"].lower()
        conf = item["confidence"]
        try:
            matched, missing, match_score = skill_gap_analysis(resume_data.get("Skills", []), career)
        except Exception:
            matched, missing, match_score = [], [], 0

        try:
            salary = predict_salary(
                role=item["role"],
                experience_years=resume_data.get("Experience (Years)", 0),
                domain=item.get("domain", ""),
                state="",
            )
        except Exception:
            salary = {"predicted_lpa": 0.0, "currency": "INR", "experience_years": 0, "role": item["role"]}

        try:
            role_score, role_feedback = role_specific_ats_score(resume_data, resume_data.get("Raw_Text", ""), career)
        except Exception:
            role_score = 0
            role_feedback = {"strengths": [], "weaknesses": [], "matched_skills": [], "missing_skills": [], "match_score": 0}

        total_required = len(matched) + len(missing)
        career_data[career] = {
            "confidence": float(conf),
            "domain": item.get("domain", ""),
            "matched_skills": matched,
            "missing_skills": missing,
            "salary": salary,
            "salary_details": salary,
            "role_ats": role_score,
            "role_ats_feedback": role_feedback,
            "skill_match_score": match_score,
            "all_skills_matched": total_required > 0 and len(missing) == 0,
            "no_skills_matched": total_required > 0 and len(matched) == 0,
            "no_skill_data": total_required == 0,
        }

    best_key = best_career.lower()
    best_data = career_data.get(best_key, next(iter(career_data.values())))

    suggestions = []
    for skill in best_data.get("missing_skills", [])[:6]:
        suggestions.append(f"Add '{skill.title()}' to strengthen alignment with the target role.")
    if confidence < 45:
           suggestions.append("Include more role-specific tools, projects, and measurable outcomes to improve career match quality.")
    if general_score < 65:
        suggestions.append("Improve section structure, action verbs, and quantified achievements for stronger ATS performance.")
    if best_data.get("role_ats", 0) < 60:
        suggestions.append("Increase domain-specific terminology and project impact statements for the predicted role.")

    return {
        "name": resume_data.get("Name", "Unknown"),
        "top3": top3,
        "labels": [c for c, _ in top3],
        "values": [float(conf) for _, conf in top3],
        "best_career": best_key,
        "confidence": float(confidence),
        "career_data": career_data,
        "matched_skills": best_data.get("matched_skills", []),
        "missing_skills": best_data.get("missing_skills", []),
        "salary": best_data.get("salary", {}),
        "salary_details": best_data.get("salary_details", {}),
        "role_ats": best_data.get("role_ats", 0),
        "all_skills_matched": best_data.get("all_skills_matched", False),
        "no_skills_matched": best_data.get("no_skills_matched", False),
        "no_skill_data": best_data.get("no_skill_data", True),
        "general_ats": general_score,
        "general_ats_feedback": general_feedback,
        "predicted_domain": prediction_bundle.get("inferred_domain", ""),
        "verdict": verdict,
        "suggestions": suggestions,
        "resume_data": resume_data,
        "ats_breakdown": {
            "structure": round(float(ats_breakdown.get("structure", 0)), 1),
            "keyword_strength": round(float(ats_breakdown.get("keywords", 0)), 1),
            "skills_depth": round(float(ats_breakdown.get("skills_depth", 0)), 1),
            "impact": round(float(ats_breakdown.get("impact", 0)), 1),
        },
    }


if __name__ == "__main__":
    path = input("Enter Resume Path: ")
    print(run_pipeline(path))
