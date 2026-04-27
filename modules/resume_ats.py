from __future__ import annotations

from .career_skill import skill_gap_analysis
import re
from typing import Dict, List, Union


# ==============================
# 🚀 ADVANCED RESUME ATS SCORING
# ==============================

action_verbs = [
    "achieved", "developed", "implemented", "led", "designed",
    "built", "managed", "created", "improved", "optimized",
    "analyzed", "delivered", "increased", "reduced", "boosted",
    "launched", "drove", "coordinated", "executed", "streamlined",
    "automated", "mentored", "resolved", "collaborated", "spearheaded",
]

_SECTION_SYNONYMS = {
    "summary": ["summary", "professional summary", "profile", "objective", "career objective"],
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic", "qualification", "educational qualifications"],
    "skills": ["skills", "technical skills", "core skills", "competencies", "expertise"],
    "projects": ["projects", "project", "key projects"],
    "certifications": ["certifications", "certification", "licenses", "training"],
}

_IMPACT_PATTERNS = [
    r"\b\d+(?:\.\d+)?%\b",
    r"\b\d+(?:\.\d+)?\s*(?:percent|percentage)\b",
    r"\b\$\s?\d+(?:[\d,]*)(?:\.\d+)?\b",
    r"\b₹\s?\d+(?:[\d,]*)(?:\.\d+)?\b",
    r"\b\d+(?:[\d,]*)(?:\.\d+)?\s*(?:users|clients|customers|students|projects|teams|branches|stores|employees|members|papers|publications|rooms)\b",
    r"\b\d+\+\b",
    r"\b(?:improved|increased|reduced|decreased|saved|grew|boosted|cut)\b.*?\b\d+(?:\.\d+)?%\b",
]

_GENERIC_SKILLS = {
    "communication", "teamwork", "leadership", "problem solving", "hard working",
    "active learner", "good listener", "analytical thinking", "ms office", "microsoft office",
}


def _safe_text(raw_text: Union[str, None]) -> str:
    return str(raw_text or "").strip()


def _clip_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 1)


def _normalize_text(raw_text: str) -> str:
    raw_text = _safe_text(raw_text).lower()
    raw_text = re.sub(r"\s+", " ", raw_text)
    return raw_text


# ==============================
# 📊 IMPACT DETECTION
# ==============================

def detect_impact(raw_text):
    raw_text = _normalize_text(raw_text)
    if not raw_text:
        return 0

    hits = sum(len(re.findall(p, raw_text)) for p in _IMPACT_PATTERNS)
    unique_metric_lines = len(set(re.findall(r"[^.!?\n]*\d[^.!?\n]*", raw_text)))
    evidence = hits + min(unique_metric_lines, 6)

    if evidence >= 10:
        return 88
    elif evidence >= 7:
        return 74
    elif evidence >= 4:
        return 58
    elif evidence >= 2:
        return 40
    elif evidence >= 1:
        return 25
    return 10


# ==============================
# 📄 STRUCTURE QUALITY
# ==============================

def structure_score(raw_text):
    raw_text_norm = _normalize_text(raw_text)
    if not raw_text_norm:
        return 0

    found_sections = 0
    for variants in _SECTION_SYNONYMS.values():
        if any(v in raw_text_norm for v in variants):
            found_sections += 1

    source_text = _safe_text(raw_text)
    has_email = bool(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", source_text, re.I))
    has_phone = bool(re.search(r"(?:\+?\d[\d\s\-()]{7,}\d)", source_text))
    has_bullets = bool(re.search(r"(?:^|\n)\s*[•\-*]", source_text))
    has_dates = len(re.findall(r"\b(?:19|20)\d{2}\b", raw_text_norm)) >= 2
    word_count = len(raw_text_norm.split())

    score = 20
    score += found_sections * 10
    if has_email:
        score += 8
    if has_phone:
        score += 7
    if has_bullets:
        score += 7
    if has_dates:
        score += 8
    if 220 <= word_count <= 900:
        score += 10
    elif 160 <= word_count <= 1200:
        score += 6

    return _clip_score(score)


# ==============================
# 🧠 KEYWORD STRENGTH
# ==============================

def keyword_score(raw_text):
    raw_text_norm = _normalize_text(raw_text)
    words = raw_text_norm.split()
    if not words:
        return 0

    matched = [word for word in action_verbs if re.search(rf"\b{re.escape(word)}\b", raw_text_norm)]
    diversity = len(set(matched))
    density = diversity / max(len(words), 1) * 1000

    score = 15 + min(diversity * 7, 42) + min(density * 8, 18)
    return _clip_score(score)


# ==============================
# 🎓 EDUCATION SCORE
# ==============================

def education_score(education_list):
    education_list = [str(e).lower() for e in education_list if e]
    if not education_list:
        return 25
    if any("phd" in e or "doctorate" in e for e in education_list):
        return 88
    elif any(x in e for e in education_list for x in ["master", "mba", "mtech", "mca", "msc", "m.s", "m.a"]):
        return 76
    elif any(x in e for e in education_list for x in ["bachelor", "btech", "bca", "bsc", "be", "b.e", "b.com", "bba", "b.s"]):
        return 64
    elif any("diploma" in e for e in education_list):
        return 50
    else:
        return 35


# ==============================
# ⏳ EXPERIENCE SCORE
# ==============================

def experience_score(years):
    try:
        years = float(years or 0)
    except Exception:
        years = 0.0

    if years >= 12:
        return 82
    elif years >= 8:
        return 74
    elif years >= 5:
        return 66
    elif years >= 3:
        return 58
    elif years >= 1:
        return 48
    else:
        return 34


# ==============================
# 📏 LENGTH QUALITY
# ==============================

def length_score(raw_text):
    word_count = len(_normalize_text(raw_text).split())
    if word_count >= 900:
        return 52
    elif word_count >= 650:
        return 68
    elif word_count >= 350:
        return 82
    elif word_count >= 220:
        return 72
    elif word_count >= 120:
        return 58
    else:
        return 35


# ==============================
# 🧠 SKILLS DEPTH
# ==============================

def _skills_depth_score(extracted_skills):
    cleaned = []
    seen = set()
    for skill in extracted_skills or []:
        s = str(skill).strip().lower()
        if not s or s in seen or len(s) < 2 or s in _GENERIC_SKILLS:
            continue
        seen.add(s)
        cleaned.append(s)

    count = len(cleaned)
    if count >= 18:
        return 86
    elif count >= 12:
        return 76
    elif count >= 8:
        return 64
    elif count >= 5:
        return 50
    elif count >= 2:
        return 36
    return 20


def _build_general_feedback(breakdown: Dict[str, float], raw_text: str, extracted_skills: List[str]):
    strengths: List[str] = []
    weaknesses: List[str] = []

    if breakdown["structure"] >= 75:
        strengths.append("Resume has a clear ATS-friendly section structure.")
    else:
        weaknesses.append("Add clearer headings like Summary, Experience, Education, and Skills.")

    if breakdown["keywords"] >= 70:
        strengths.append("Strong use of action verbs improves keyword relevance.")
    else:
        weaknesses.append("Use more action verbs such as developed, led, built, optimized, and improved.")

    if breakdown["skills_depth"] >= 70:
        strengths.append("Technical skill coverage is strong and easy to detect.")
    else:
        weaknesses.append("Add more role-specific tools, platforms, and technical skills explicitly.")

    if breakdown["impact"] >= 65:
        strengths.append("Quantified achievements are present and improve ATS value.")
    else:
        weaknesses.append("Add measurable impact like percentages, counts, savings, or growth outcomes.")

    if len(_normalize_text(raw_text).split()) < 180:
        weaknesses.append("Resume content is short; add more project and achievement details.")
    if len(extracted_skills or []) <= 3:
        weaknesses.append("Skill extraction is shallow; mention tools and technologies more explicitly.")

    return {
        "strengths": strengths[:4],
        "weaknesses": weaknesses[:4],
    }


# ==============================
# 🧠 GENERAL ATS SCORE
# ==============================

def general_ats_score(resume_data, raw_text=None, extracted_skills=None, experience=None):
    """Supports both existing project call styles and returns (score, feedback_dict)."""
    if isinstance(resume_data, dict):
        raw_text = _safe_text(raw_text if raw_text is not None else resume_data.get("Raw_Text", ""))
        extracted_skills = list(extracted_skills if extracted_skills is not None else resume_data.get("Skills", []))
        education_list = resume_data.get("Education", [])
        experience_years = experience if experience is not None else resume_data.get("Experience (Years)", 0)
    else:
        raw_text = _safe_text(resume_data)
        extracted_skills = list(extracted_skills or [])
        education_list = []
        experience_years = experience if experience is not None else 0

    breakdown = {
        "structure": structure_score(raw_text),
        "keywords": keyword_score(raw_text),
        "skills_depth": _skills_depth_score(extracted_skills),
        "impact": detect_impact(raw_text),
        "education": education_score(education_list),
        "experience": experience_score(experience_years),
        "length": length_score(raw_text),
    }

    score = (
        breakdown["structure"] * 0.24
        + breakdown["keywords"] * 0.14
        + breakdown["skills_depth"] * 0.22
        + breakdown["impact"] * 0.18
        + breakdown["education"] * 0.07
        + breakdown["experience"] * 0.09
        + breakdown["length"] * 0.06
    )
    score = _clip_score(score)
    feedback = _build_general_feedback(breakdown, raw_text, extracted_skills)
    feedback["breakdown"] = breakdown
    return score, feedback


# ==============================
# 🎯 ROLE-SPECIFIC ATS
# ==============================

def role_specific_ats_score(resume_data, raw_text=None, role=None):
    """Supports both existing project call styles and returns (score, feedback_dict)."""
    if isinstance(resume_data, dict):
        extracted_skills = resume_data.get("Skills", [])
        source_text = _safe_text(raw_text if raw_text is not None else resume_data.get("Raw_Text", ""))
        target_role = str(role or "").strip()
    else:
        extracted_skills = []
        source_text = _safe_text(resume_data)
        target_role = str(raw_text or "").strip()  # 2-arg style: (raw_text, role)

    if not target_role:
        return 0.0, {
            "strengths": [],
            "weaknesses": ["Target role missing."],
            "matched_skills": [],
            "missing_skills": [],
            "match_score": 0.0,
        }

    matched, missing, match_score = skill_gap_analysis(extracted_skills, target_role)

    role_tokens = [tok for tok in re.split(r"\W+", target_role.lower()) if len(tok) > 2]
    source_norm = _normalize_text(source_text)
    role_keyword_hits = sum(1 for tok in role_tokens if re.search(rf"\b{re.escape(tok)}\b", source_norm))
    role_keyword_score = min(70.0, role_keyword_hits * 18.0)

    final_score = _clip_score(match_score * 0.75 + role_keyword_score * 0.25)
    strengths = []
    weaknesses = []
    if match_score >= 70:
        strengths.append("Resume already matches many required role skills.")
    elif match_score >= 40:
        strengths.append("Resume shows partial alignment with the target role.")
    else:
        weaknesses.append("Core skill match for the target role is still limited.")

    if role_keyword_hits >= 2:
        strengths.append("Target role terminology appears in the resume.")
    else:
        weaknesses.append("Add target-role terms to projects, summaries, or experience bullets.")

    if missing:
        weaknesses.append("Missing role skills should be added through projects, tools, or certifications.")

    return final_score, {
        "strengths": strengths[:3],
        "weaknesses": weaknesses[:3],
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score": match_score,
    }


# ==============================
# 🧾 VERDICT
# ==============================

def ats_verdict(score, role_score=None):
    try:
        score = float(score or 0)
    except Exception:
        score = 0.0
    try:
        role_score = None if role_score is None else float(role_score)
    except Exception:
        role_score = None

    effective = score if role_score is None else (score * 0.7 + role_score * 0.3)

    if effective >= 82:
        return "🔥 Excellent Resume — Top Tier Candidate"
    elif effective >= 68:
        return "✅ Strong Resume — Ready for Interviews"
    elif effective >= 54:
        return "⚠ Good Resume — Needs Optimization"
    elif effective >= 40:
        return "❗ Average Resume — Improve Skills & Impact"
    else:
        return "🚫 Weak Resume — Major Improvements Needed"
