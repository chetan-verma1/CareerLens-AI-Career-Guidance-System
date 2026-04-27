from __future__ import annotations

import os
import re
from collections import OrderedDict
from datetime import datetime, UTC
from typing import Dict, List, Optional, Tuple

import pdfplumber
from docx import Document

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

from rapidfuzz import fuzz, process

from modules.skill_db import skill_database

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}
CURRENT_DATE = datetime.now(UTC)
MAX_REASONABLE_EXPERIENCE = 45.0

SECTION_KEYWORDS = OrderedDict({
    "summary": ["summary", "profile", "objective", "professional summary", "career objective", "about me"],
    "experience": ["experience", "work experience", "employment", "professional experience", "experience details", "internship", "internships", "work history"],
    "education": ["education", "education summary", "academic background", "academics", "qualification", "qualifications", "academic qualifications"],
    "skills": ["skills", "technical skills", "core competencies", "competencies", "technologies", "tools", "skill set", "key skills"],
    "projects": ["projects", "project experience", "academic projects", "projects undertaken"],
    "certifications": ["certifications", "certificates", "licenses", "trainings", "courses"],
})

EDU_CANONICAL_PATTERNS = OrderedDict([
    (r"\bph\.?d\b|\bdoctorate\b|\bdoctor of philosophy\b", "Ph.D"),
    (r"\bm\.?phil\b|\bmaster of philosophy\b", "M.Phil"),
    (r"\bm\.?tech\b|\bmaster of technology\b", "M.Tech"),
    (r"\bm\.?e\b|\bmaster of engineering\b", "M.E"),
    (r"\bm\.?sc\b|\bmaster of science\b", "M.Sc"),
    (r"\bm\.?ca\b|\bmaster of computer applications?\b", "MCA"),
    (r"\bmba\b|\bmaster of business administration\b", "MBA"),
    (r"\bm\.?com\b|\bmaster of commerce\b", "M.Com"),
    (r"\bmasters?\b", "Master"),
    (r"\bb\.?tech\b|\bbachelor of technology\b", "B.Tech"),
    (r"\bb\.e\b|\bb\.e\.\b|\bbachelor of engineering\b", "B.E"),
    (r"\bb\.?s\b|\bb\.?sc\b|\bbachelor of science\b", "B.Sc"),
    (r"\bb\.?ca\b|\bbachelor of computer applications?\b", "BCA"),
    (r"\bb\.b\.a\b|\bbba\b|\bbachelor of business administration\b", "BBA"),
    (r"\bb\.?com\b|\bbachelor of commerce\b", "B.Com"),
    (r"\bb\.?ed\b|\bbachelor of education\b", "B.Ed"),
    (r"\bb\.?a\b|\bbachelor of arts\b", "Bachelor"),
    (r"\bbachelors?\b", "Bachelor"),
    (r"\bdiploma\b|\bpolytechnic\b", "Diploma"),
    (r"\bcertificate(?: in)? [a-z &]+\b|\bcertification\b", "Certificate"),
    (r"\b10\+2\b|\b12th\b|\bclass 12\b|\bintermediate\b|\bhigher secondary\b", "12th"),
    (r"\b10th\b|\bclass 10\b|\bmatric(?:ulation)?\b|\bsecondary school\b", "10th"),
])

EDUCATION_CONTEXT_WORDS = {
    "university", "college", "institute", "school", "academy", "board", "campus", "faculty", "department",
    "degree", "cgpa", "gpa", "percentage", "marks", "major", "minor", "graduation", "post graduation"
}
NON_EDUCATION_CONTEXT_WORDS = {
    "skills", "experience", "employment", "worked", "responsible", "project", "projects", "tool", "tools",
    "technical", "languages", "software", "framework", "internship", "developer", "engineer", "manager"
}
EDUCATION_ORDER = {
    "Ph.D": 100, "M.Phil": 95, "M.Tech": 90, "M.E": 88, "M.Sc": 86, "MCA": 84, "MBA": 82, "M.Com": 80, "Master": 78,
    "B.Tech": 70, "B.E": 68, "B.Sc": 66, "BCA": 64, "BBA": 62, "B.Com": 60, "B.Ed": 58, "Bachelor": 56,
    "Diploma": 40, "Certificate": 30, "12th": 20, "10th": 10,
}

NAME_BLOCKLIST = {
    "resume", "curriculum vitae", "cv", "profile", "summary", "objective", "contact", "address", "phone", "email", "skills", "experience", "education", "dob", "current positions", "course", "institution", "university"
}

GENERIC_SKILL_BLACKLIST = {
    "analysis", "analytics", "communication", "leadership", "management", "operations", "engineering", "law", "banking", "insurance", "humanities", "governance", "research", "teaching", "design", "architecture", "compliance", "coaching", "collaboration", "entrepreneurship", "software teaching",
    "data", "support", "education", "editing", "consulting", "planning", "security", "insights", "accuracy", "engagement", "integrity", "organization", "mentorship", "training", "listening", "mathematics", "sales", "reporting"
}

COMMON_MULTIWORD_SKILLS = {
    "machine learning", "deep learning", "data science", "computer vision", "natural language processing", "power bi",
    "problem solving", "project management", "business analysis", "financial modeling", "digital marketing", "network security",
    "academic writing", "content marketing", "data analysis", "feature engineering", "model deployment", "data visualization",
    "manual testing", "business intelligence", "software testing", "operating systems", "sql server", "ms access"
}



STRONG_SINGLE_TOKEN_SKILLS = {
    "python", "java", "sql", "excel", "tableau", "power bi", "php", "docker", "kubernetes", "aws", "azure",
    "linux", "oracle", "mysql", "postgresql", "sap", "spss", "react", "django", "flask", "golang", "go",
    "c", "c++", "c#", ".net", "html", "css", "javascript", "typescript", "r", "tensorflow", "pytorch",
    "splunk", "siem", "jira", "git", "figma", "graphql"
}


def _is_ascii_text(value: str) -> bool:
    try:
        value.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def _is_specific_skill(value: str) -> bool:
    value = (value or "").strip().lower()
    if not value or not _is_ascii_text(value):
        return False
    if value in GENERIC_SKILL_BLACKLIST:
        return False
    if len(value) < 2:
        return False
    if len(value.split()) == 1 and value not in STRONG_SINGLE_TOKEN_SKILLS and len(value) < 4:
        return False
    return True

OPTIONAL_OCR_AVAILABLE = False
try:
    import pytesseract  # type: ignore
    from pdf2image import convert_from_path  # type: ignore
    OPTIONAL_OCR_AVAILABLE = True
except Exception:
    pytesseract = None
    convert_from_path = None


def clean_text(text: str) -> str:
    text = str(text or "")
    text = text.replace("\x0c", "\n")
    text = re.sub(r"\u2022|\u25cf|\u25aa|\u25e6|•", " - ", text)
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("c++", "cplusplus").replace("c#", "csharp").replace(".net", "dotnet")
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(file_path: str) -> str:
    chunks: List[str] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    chunks.append(page_text)
    except Exception:
        pass

    if sum(len(c) for c in chunks) < 120 and PdfReader is not None:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    chunks.append(page_text)
        except Exception:
            pass

    if sum(len(c) for c in chunks) < 120 and OPTIONAL_OCR_AVAILABLE:
        try:
            images = convert_from_path(file_path)
            for image in images:
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    chunks.append(ocr_text)
        except Exception:
            pass

    return clean_text("\n".join(chunks))


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return clean_text("\n".join(paragraphs))


def is_resume(text: str) -> bool:
    normalized = normalize_text(text)
    keys = ["education", "experience", "skills", "projects", "summary", "objective", "employment"]
    hits = sum(1 for key in keys if key in normalized)
    return hits >= 2 or len(normalized.split()) > 100


def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def extract_name(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    top_lines = lines[:12]
    for line in top_lines:
        simple = re.sub(r"[^A-Za-z .]", "", line).strip()
        lower = simple.lower()
        if not simple or lower in NAME_BLOCKLIST:
            continue
        if any(token in line.lower() for token in ["@", "http", "linkedin", "github", "portfolio", "address", "dob", "phone", "mobile", "email", "sector", "tel:"]):
            continue
        words = [w for w in simple.split() if w]
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w[0].isalpha()):
            return " ".join(words)
        if simple.isupper() and 2 <= len(words) <= 4:
            return simple.title()

    email = _extract_email(text)
    if email:
        username = email.split("@")[0]
        username = re.sub(r"[._\-]+", " ", username)
        username = re.sub(r"\d+", "", username).strip()
        parts = [p for p in username.split() if p]
        if 1 < len(parts) <= 3:
            return " ".join(p.capitalize() for p in parts)
    return "Candidate"


def _is_section_header(line: str) -> Optional[str]:
    normalized = normalize_text(re.sub(r"[:\-–]+$", "", line))
    for section, keywords in SECTION_KEYWORDS.items():
        for keyword in keywords:
            key = normalize_text(keyword)
            if normalized == key or normalized.startswith(key + " "):
                return section
    return None


def split_sections(text: str) -> Dict[str, str]:
    lines = [line.strip() for line in text.splitlines()]
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"
    for line in lines:
        if not line:
            continue
        matched_section = _is_section_header(line)
        if matched_section:
            current = matched_section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items() if value}


def _build_skill_lexicon() -> Dict[str, str]:
    lexicon: Dict[str, str] = {}
    for skill in skill_database:
        value = str(skill or "").strip()
        if not value:
            continue
        canonical = re.sub(r"\s+", " ", value).strip().lower()
        canonical = canonical.replace("cplusplus", "c++").replace("csharp", "c#").replace("dotnet", ".net")
        if not _is_specific_skill(canonical):
            continue
        lexicon[normalize_text(canonical)] = canonical
    for skill in COMMON_MULTIWORD_SKILLS:
        if _is_specific_skill(skill):
            lexicon[normalize_text(skill)] = skill
    aliases = {
        "js": "javascript", "ts": "typescript", "py": "python", "ml": "machine learning", "nlp": "nlp",
        "cv": "computer vision", "powerbi": "power bi", "node": "node.js", "nodejs": "node.js",
        "reactjs": "react", "postgres": "postgresql", "ms excel": "excel", "m s excel": "excel",
    }
    for alias, canonical in aliases.items():
        if _is_specific_skill(canonical):
            lexicon[normalize_text(alias)] = canonical
    return lexicon


SKILL_LEXICON = _build_skill_lexicon()
SKILL_KEYS = list(SKILL_LEXICON.keys())


def _candidate_skill_phrases(text: str) -> List[str]:
    candidates: List[str] = []
    for line in text.splitlines():
        line = line.strip(" :-\t")
        if not line:
            continue
        parts = re.split(r"[|,/;•\t]", line)
        for part in parts:
            p = normalize_text(part)
            if not p:
                continue
            candidates.append(p)
            words = p.split()
            for n in [1, 2, 3]:
                for i in range(len(words) - n + 1):
                    gram = " ".join(words[i:i+n])
                    if 2 <= len(gram) <= 40:
                        candidates.append(gram)
    return list(dict.fromkeys(candidates))


def extract_skills(text: str, sections: Optional[Dict[str, str]] = None) -> List[str]:
    sections = sections or split_sections(text)
    primary_source = "\n".join(filter(None, [sections.get("skills", ""), sections.get("projects", ""), sections.get("certifications", "")]))
    secondary_source = "\n".join(filter(None, [sections.get("experience", ""), sections.get("summary", "")]))
    fallback_source = text[:4000]
    found: OrderedDict[str, None] = OrderedDict()

    for source, allow_generic in [(primary_source, True), (secondary_source, False)]:
        if not source.strip():
            continue
        normalized_source = normalize_text(source)
        for key, canonical in SKILL_LEXICON.items():
            if not _is_specific_skill(canonical):
                continue
            if canonical in GENERIC_SKILL_BLACKLIST and not allow_generic:
                continue
            pattern = r"(?<!\w)" + re.escape(key) + r"(?!\w)"
            if re.search(pattern, normalized_source):
                found[canonical] = None

    fuzzy_source = primary_source or secondary_source
    for candidate in _candidate_skill_phrases(fuzzy_source):
        if candidate in SKILL_LEXICON:
            found[SKILL_LEXICON[candidate]] = None
            continue
        match = process.extractOne(candidate, SKILL_KEYS, scorer=fuzz.WRatio, score_cutoff=96)
        if match and _is_specific_skill(SKILL_LEXICON[match[0]]):
            found[SKILL_LEXICON[match[0]]] = None

    if len(found) < 8:
        normalized_source = normalize_text(fallback_source)
        for key, canonical in SKILL_LEXICON.items():
            if not _is_specific_skill(canonical) or len(key) < 3:
                continue
            pattern = r"(?<!\w)" + re.escape(key) + r"(?!\w)"
            if re.search(pattern, normalized_source):
                found[canonical] = None
            if len(found) >= 40:
                break

    cleaned = []
    for skill in found.keys():
        s = skill.replace("cplusplus", "c++").replace("csharp", "c#").replace("dotnet", ".net")
        if _is_specific_skill(s):
            cleaned.append(s)
    return sorted(set(cleaned), key=lambda x: (len(x.split()), x))[:80]


def _education_candidate_lines(text: str, sections: Dict[str, str]) -> List[Tuple[str, int]]:
    lines: List[Tuple[str, int]] = []
    education_section = sections.get("education", "")
    if education_section.strip():
        for line in education_section.splitlines():
            stripped = line.strip()
            if stripped:
                lines.append((stripped, 4))

    preview = "\n".join(text.splitlines()[:80])
    for line in preview.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        normalized = normalize_text(stripped)
        has_context = any(word in normalized for word in EDUCATION_CONTEXT_WORDS)
        has_degree = any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in EDU_CANONICAL_PATTERNS)
        if has_context or has_degree:
            lines.append((stripped, 1))

    best: OrderedDict[str, int] = OrderedDict()
    for line, score in lines:
        prev = best.get(line)
        if prev is None or score > prev:
            best[line] = score
    return list(best.items())


def extract_education(text: str, sections: Optional[Dict[str, str]] = None) -> List[str]:
    sections = sections or split_sections(text)
    found_scores: Dict[str, int] = {}

    for raw_line, base_score in _education_candidate_lines(text, sections):
        normalized = normalize_text(raw_line)
        if not normalized:
            continue
        line_score = base_score
        if any(word in normalized for word in EDUCATION_CONTEXT_WORDS):
            line_score += 2
        if any(word in normalized for word in NON_EDUCATION_CONTEXT_WORDS):
            line_score -= 2
        for pattern, label in EDU_CANONICAL_PATTERNS.items():
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                found_scores[label] = max(found_scores.get(label, 0), line_score + 2)

    if not found_scores and not sections.get("education", "").strip():
        normalized_preview = normalize_text("\n".join(text.splitlines()[:80]))
        for pattern, label in EDU_CANONICAL_PATTERNS.items():
            if re.search(pattern, normalized_preview, flags=re.IGNORECASE):
                found_scores[label] = 2

    found_scores = {label: score for label, score in found_scores.items() if score >= 3}
    labels = list(found_scores.keys())
    if any(label in labels for label in {"B.Tech", "B.E", "B.Sc", "BCA", "BBA", "B.Com", "B.Ed"}):
        found_scores.pop("Bachelor", None)
    if any(label in labels for label in {"M.Tech", "M.E", "M.Sc", "MCA", "MBA", "M.Com", "M.Phil", "Ph.D"}):
        found_scores.pop("Master", None)

    ordered = sorted(found_scores, key=lambda x: (-found_scores[x], -EDUCATION_ORDER.get(x, 0), x))
    return ordered[:8]


def _parse_month_token(token: Optional[str]) -> Optional[int]:
    if not token:
        return None
    return MONTHS.get(token.strip().lower().replace(".", ""))


def _parse_year_token(token: Optional[str]) -> Optional[int]:
    if not token:
        return None
    token = token.strip()
    if re.fullmatch(r"\d{4}", token):
        year = int(token)
        if 1950 <= year <= CURRENT_DATE.year + 1:
            return year
    return None


def _date_to_month_index(month: int, year: int) -> int:
    return year * 12 + month


def _safe_experience_value(years: float) -> Optional[float]:
    return round(years, 2) if 0 <= years <= MAX_REASONABLE_EXPERIENCE else None


def _months_to_years(months: int) -> float:
    return round(months / 12.0, 2)


def _extract_total_experience_mentions(text: str) -> List[float]:
    values: List[float] = []
    normalized = clean_text(text)
    patterns = [
        r"(?P<years>\d{1,2})\s+years?(?:\s+and\s+(?P<months>\d{1,2})\s+months?)?",
        r"(?P<years>\d{1,2})\+?\s+yrs?(?:\s+(?P<months>\d{1,2})\s+mos?)?",
    ]
    anchors = ["experience", "teaching", "software development", "current employer", "present employer", "total"]
    for pattern in patterns:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            context_before = normalized[max(0, match.start() - 64):match.start()].lower()
            context_after = normalized[match.end():min(len(normalized), match.end() + 32)].lower()
            context = f"{context_before} {context_after}"
            if not any(anchor in context for anchor in anchors):
                continue
            years = float(match.group("years"))
            months = float(match.groupdict().get("months") or 0)
            value = _safe_experience_value(years + months / 12.0)
            if value is not None:
                values.append(value)
    return values


def _extract_range_spans(text: str) -> List[Tuple[int, int]]:
    patterns = [
        r"(?P<sd>\d{1,2})[-/\s](?P<sm>[A-Za-z]{3,9})[-/\s](?P<sy>\d{4})\s*(?:to|\-|–)\s*(?:(?P<ed>\d{1,2})[-/\s](?P<em>[A-Za-z]{3,9})[-/\s](?P<ey>\d{4})|(?P<present>present|current|till date|till now|now))",
        r"(?P<sm>[A-Za-z]{3,9})(?:\s+\d{1,2})?(?:,)?\s+(?P<sy>\d{4})\s*(?:to|\-|–|through)\s*(?:(?P<em>[A-Za-z]{3,9})(?:\s+\d{1,2})?(?:,)?\s+(?P<ey>\d{4})|(?P<present>present|current|now))",
        r"(?P<sm>[A-Za-z]{3,9})(?:\s+\d{1,2})?(?:,)?\s+(?P<sy>\d{4})\s+till\s+(?P<present>date|present|current|now)",
        r"(?P<sy>\d{4})\s*(?:to|\-|–)\s*(?P<ey>\d{4}|present|current|now)",
    ]
    spans: List[Tuple[int, int]] = []
    source = clean_text(text)
    for pattern in patterns:
        for match in re.finditer(pattern, source, flags=re.IGNORECASE):
            gd = match.groupdict()
            sy = _parse_year_token(gd.get("sy"))
            if not sy:
                continue
            sm = _parse_month_token(gd.get("sm")) or 1
            if (gd.get("present") or "").strip().lower() in {"present", "current", "till date", "till now", "now", "date"}:
                ey = CURRENT_DATE.year
                em = CURRENT_DATE.month
            else:
                ey_raw = gd.get("ey")
                if ey_raw and ey_raw.lower() in {"present", "current", "now"}:
                    ey = CURRENT_DATE.year
                    em = CURRENT_DATE.month
                else:
                    ey = _parse_year_token(ey_raw)
                    em = _parse_month_token(gd.get("em")) or 12
            if not ey or sy > ey or sy < 1950 or ey > CURRENT_DATE.year + 1:
                continue
            start_i = _date_to_month_index(sm, sy)
            end_i = _date_to_month_index(em, ey)
            if end_i >= start_i:
                spans.append((start_i, end_i))
    return spans


def _merge_spans(spans: List[Tuple[int, int]]) -> int:
    if not spans:
        return 0
    spans = sorted(spans)
    merged = [list(spans[0])]
    for start, end in spans[1:]:
        last = merged[-1]
        if start <= last[1] + 1:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return sum(end - start + 1 for start, end in merged)


def extract_experience(text: str, sections: Optional[Dict[str, str]] = None) -> float:
    sections = sections or split_sections(text)
    section_source = "\n".join(filter(None, [sections.get("experience", ""), sections.get("projects", "")]))
    explicit_values = _extract_total_experience_mentions(text)
    estimated = _safe_experience_value(_months_to_years(_merge_spans(_extract_range_spans(section_source or text))))
    full_text_estimated = _safe_experience_value(_months_to_years(_merge_spans(_extract_range_spans(text))))
    best_explicit = max(explicit_values) if explicit_values else None
    if best_explicit is not None and estimated is not None:
        return best_explicit if abs(best_explicit - estimated) <= 3.0 or best_explicit > estimated else estimated
    if best_explicit is not None:
        return best_explicit
    if estimated is not None and full_text_estimated is not None:
        return max(estimated, full_text_estimated)
    if estimated is not None:
        return estimated
    if full_text_estimated is not None:
        return full_text_estimated
    return 0.0


def analyze_resume(file_path: str) -> Dict[str, object]:
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif extension == ".docx":
        raw_text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
    if not raw_text.strip() or not is_resume(raw_text):
        return {"Name": "Candidate", "Skills": [], "Experience (Years)": 0, "Education": [], "Raw_Text": raw_text}
    sections = split_sections(raw_text)
    return {
        "Name": extract_name(raw_text),
        "Skills": extract_skills(raw_text, sections),
        "Experience (Years)": extract_experience(raw_text, sections),
        "Education": extract_education(raw_text, sections),
        "Raw_Text": raw_text,
    }


if __name__ == "__main__":
    sample = input("Enter resume path: ").strip()
    print(analyze_resume(sample))
