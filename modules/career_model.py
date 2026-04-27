from __future__ import annotations

import math
import os
import re
from difflib import SequenceMatcher, get_close_matches
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ROLE_PROFILE_PATH = os.path.join(DATA_DIR, "career_role_profiles.csv")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EDUCATION_PRIORITY = [
    "phd",
    "doctorate",
    "mtech",
    "msc",
    "mca",
    "mba",
    "masters",
    "master",
    "pgdm",
    "llm",
    "mphil",
    "btech",
    "be",
    "bachelor",
    "bsc",
    "bca",
    "bba",
    "bcom",
    "llb",
    "bdes",
    "bfa",
    "diploma",
    "12th",
    "10th",
]

# Aliases for user-typed shorthand → canonical skill tokens
_SKILL_ALIASES: Dict[str, str] = {
    "ml":               "machine learning",
    "dl":               "deep learning",
    "k8s":              "kubernetes",
    "tf":               "tensorflow",
    "pt":               "pytorch",
    "nlp":              "natural language processing",
    "cv":               "computer vision",
    "ci/cd":            "ci cd",
    "cicd":             "ci cd",
    "devops":           "devops",
    "gcp":              "gcp",
    "aws":              "aws",
    "llm":              "llm",
    "gen ai":           "generative ai",
    "genai":            "generative ai",
    "ui/ux":            "ui ux",
    "uiux":             "ui ux",
    "oop":              "object oriented programming",
    "dsa":              "data structures",
    "js":               "javascript",
    "ts":               "typescript",
    "react.js":         "react",
    "reactjs":          "react",
    "node.js":          "node.js",
    "nodejs":           "node.js",
    "sql server":       "sql",
    "postgresql":       "postgresql",
    "postgres":         "postgresql",
    "c plus plus":      "cplusplus",
    "c sharp":          "csharp",
    "dotnet":           "dotnet",
    "dot net":          "dotnet",
    "r language":       "r",
    "power bi":         "power bi",
    "powerbi":          "power bi",
    "tableau":          "tableau",
    "erp":              "erp",
    "sap":              "sap",
    "six sigma":        "six sigma",
    "pmp":              "project management",
    "agile":            "agile",
    "scrum":            "scrum",
    "vlsi":             "vlsi",
    "fpga":             "fpga",
    "ros":              "ros",
    "gis":              "gis",
    "ehr":              "ehr",
    "siem":             "siem",
    "cad":              "cad",
    "cfd":              "cfd",
    "fea":              "fea",
    "hvac":             "hvac",
}

# Ensemble weight configuration
_W_TFIDF_FULL   = 0.30
_W_TFIDF_SKILLS = 0.20
_W_SKILL_IDF    = 0.30
_W_EDUCATION    = 0.07
_W_EXPERIENCE   = 0.07
_W_DOMAIN_KW    = 0.06

# Softmax temperature (lower → wider spread, higher → softer)
_SOFTMAX_TEMP = 4.0

# Fuzzy match threshold for skill expansion (0-1 scale)
_FUZZY_THRESHOLD = 0.72

# Tie-break band: roles within this score gap trigger disambiguation
_TIEBREAK_BAND = 0.04


_SUPPORT_FLOOR = 0.12
_LOW_SUPPORT_THRESHOLD = 0.18
_MIN_DOMAIN_HITS = 2


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

def clean_text(text: Union[str, Iterable[str], None]) -> str:
    """Normalise raw text into a clean lowercase token string."""
    if text is None:
        return ""
    if isinstance(text, (list, tuple, set)):
        text = " ".join(str(item) for item in text if item)
    text = str(text).lower()
    # Preserve common tech tokens before stripping punctuation
    text = text.replace("c++", "cplusplus").replace("c#", "csharp").replace(".net", "dotnet")
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _expand_skill_aliases(skills: List[str]) -> List[str]:
    """Expand shorthand skill tokens to canonical forms and deduplicate."""
    expanded: List[str] = []
    seen: set = set()
    for sk in skills:
        sk_clean = clean_text(sk)
        canonical = _SKILL_ALIASES.get(sk_clean, sk_clean)
        if canonical and canonical not in seen:
            seen.add(canonical)
            expanded.append(canonical)
        # Also keep original if different
        if sk_clean and sk_clean != canonical and sk_clean not in seen:
            seen.add(sk_clean)
            expanded.append(sk_clean)
    return expanded


def _split_pipe_or_csv(value: str) -> List[str]:
    """Split a pipe- or comma-separated value into cleaned tokens."""
    if not value or (isinstance(value, float) and math.isnan(value)):
        return []
    parts = re.split(r"\||,", str(value))
    return [clean_text(p) for p in parts if clean_text(p)]


# ---------------------------------------------------------------------------
# Data loading  (cached for zero reload cost in production)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_role_profiles() -> pd.DataFrame:
    """Load and enrich career_role_profiles.csv. Cached after first call."""
    df = pd.read_csv(ROLE_PROFILE_PATH)
    df.columns = [str(c).strip() for c in df.columns]
    required = [
        "Role", "Domain", "Aliases", "Description",
        "Skills", "Education", "Experience_Min", "Experience_Max", "Keywords",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"career_role_profiles.csv missing columns: {missing}")

    df = df.fillna("")

    # Cleaned scalar fields
    df["role_clean"]   = df["Role"].map(clean_text)
    df["domain_clean"] = df["Domain"].map(clean_text)

    # List fields
    df["aliases_list"]   = df["Aliases"].map(_split_pipe_or_csv)
    df["skills_list"]    = df["Skills"].map(_split_pipe_or_csv)
    df["education_list"] = df["Education"].map(_split_pipe_or_csv)
    df["keywords_list"]  = df["Keywords"].map(_split_pipe_or_csv)

    # Full-profile text blob for TF-IDF corpus A
    df["profile_text"] = df.apply(
        lambda row: " ".join(filter(None, [
            clean_text(row["Role"]),
            clean_text(row["Domain"]),
            " ".join(row["aliases_list"]),
            clean_text(row["Description"]),
            " ".join(row["skills_list"]),
            " ".join(row["education_list"]),
            " ".join(row["keywords_list"]),
        ])),
        axis=1,
    )

    # Skills-only text blob for TF-IDF corpus B (boosted discriminator)
    df["skills_text"] = df.apply(
        lambda row: " ".join(
            row["skills_list"] + row["keywords_list"] + row["aliases_list"]
        ),
        axis=1,
    )

    return df


# ---------------------------------------------------------------------------
# Pre-computed IDF weight per skill token across all role profiles
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _skill_idf_map() -> Dict[str, float]:
    """
    Compute an IDF weight for every skill token that appears in the corpus.
    Skill tokens that appear in many roles get low IDF (common → not discriminative).
    Skill tokens unique to 1–2 roles get high IDF (rare → highly discriminative).

    IDF formula: log((1 + N) / (1 + df)) + 1   (sklearn smooth IDF style)
    """
    profiles = _load_role_profiles()
    N = len(profiles)
    skill_doc_freq: Dict[str, int] = {}
    for skills in profiles["skills_list"]:
        for sk in skills:
            skill_doc_freq[sk] = skill_doc_freq.get(sk, 0) + 1
    # Also count keywords as weak skill proxies
    for kws in profiles["keywords_list"]:
        for kw in kws:
            skill_doc_freq[kw] = skill_doc_freq.get(kw, 0) + 0.3  # fractional — less weight

    idf_map: Dict[str, float] = {}
    for token, df_count in skill_doc_freq.items():
        idf_map[token] = math.log((1 + N) / (1 + df_count)) + 1.0
    return idf_map


# ---------------------------------------------------------------------------
# TF-IDF vectoriser bundle  (two separate spaces)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _role_vectorizer_bundle():
    """
    Returns (vectorizer_full, matrix_full, vectorizer_skills, matrix_skills).

    vectorizer_full   – trained on full profile_text (roles × 12k features)
    vectorizer_skills – trained on skills_text only   (roles × 5k features)
    """
    profiles = _load_role_profiles()

    # Full-profile vectoriser: bigrams, light stop-word removal
    vf = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        min_df=1,
        max_features=12000,
        sublinear_tf=True,
    )
    mf = vf.fit_transform(profiles["profile_text"].tolist())

    # Skills-only vectoriser: unigrams + bigrams, no stop-word removal
    # (tech abbreviations like 'c' would be removed otherwise)
    vs = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words=None,
        min_df=1,
        max_features=5000,
        sublinear_tf=True,
    )
    ms = vs.fit_transform(profiles["skills_text"].tolist())

    return vf, mf, vs, ms


# ---------------------------------------------------------------------------
# Domain → keyword map  (for domain inference)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _domain_keyword_map() -> Dict[str, List[str]]:
    """
    Build a mapping {domain → list of characteristic tokens} for domain inference.
    Each token list includes role names, aliases, skills, and keywords.
    """
    profiles = _load_role_profiles()
    mapping: Dict[str, List[str]] = {}
    for domain, group in profiles.groupby("Domain"):
        tokens: List[str] = []
        for _, row in group.iterrows():
            tokens.extend(row["skills_list"])          # ALL skills, not just first 12
            tokens.extend(row["keywords_list"])        # ALL keywords
            tokens.extend(row["aliases_list"])
            tokens.append(clean_text(row["Role"]))
            # Also add individual words from role name for partial matching
            for word in clean_text(row["Role"]).split():
                if len(word) > 3:
                    tokens.append(word)
        seen: List[str] = []
        used: set = set()
        for token in tokens:
            token = clean_text(token)
            if token and token not in used and len(token) > 2:
                used.add(token)
                seen.append(token)
        mapping[domain] = seen[:60]
    return mapping


# ---------------------------------------------------------------------------
# Education scoring
# ---------------------------------------------------------------------------

def _education_rank(education_items: Iterable[str]) -> int:
    """
    Return a numeric rank for the highest qualification found in the items.
    Higher = more qualified.  0 = nothing recognised.
    """
    joined = clean_text(list(education_items))
    total = len(EDUCATION_PRIORITY)
    for idx, token in enumerate(EDUCATION_PRIORITY, start=1):
        if token in joined:
            return total - idx + 1
    return 0


# ---------------------------------------------------------------------------
# Fuzzy skill matching
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _all_role_skill_tokens() -> List[str]:
    """Flat list of all unique skill tokens across the corpus (for fuzzy matching)."""
    profiles = _load_role_profiles()
    tokens: set = set()
    for skills in profiles["skills_list"]:
        tokens.update(skills)
    for kws in profiles["keywords_list"]:
        tokens.update(kws)
    return sorted(tokens)


def _fuzzy_expand_skills(user_skills: List[str]) -> List[str]:
    """
    For each user skill token that does not directly appear in the corpus,
    find the closest corpus skill via SequenceMatcher and append it if the
    similarity exceeds _FUZZY_THRESHOLD.

    This means "deep learning frameworks" expands to include "deep learning",
    "k8s" expands to "kubernetes", etc.
    """
    corpus_tokens = _all_role_skill_tokens()
    expanded = list(user_skills)
    for sk in user_skills:
        if sk not in corpus_tokens:
            matches = get_close_matches(sk, corpus_tokens, n=2, cutoff=_FUZZY_THRESHOLD)
            for m in matches:
                if m not in expanded:
                    expanded.append(m)
    return expanded


# ---------------------------------------------------------------------------
# Skill IDF score for a given user↔role pair
# ---------------------------------------------------------------------------

def _compute_skill_idf_score(
    user_skills: List[str],
    role_skills: List[str],
    idf_map: Dict[str, float],
) -> float:
    """
    Weighted Jaccard-style overlap where each matching skill is weighted by
    its IDF (rarity) score. Normalised to [0, 1].

    Formula:
        numerator   = Σ IDF(sk) for sk in (user ∩ role)
        denominator = Σ IDF(sk) for sk in role_skills
    """
    user_set = set(user_skills)
    role_set = set(role_skills)
    matched = user_set & role_set

    denom = sum(idf_map.get(sk, 1.0) for sk in role_set)
    if denom == 0:
        return 0.0
    numer = sum(idf_map.get(sk, 1.0) for sk in matched)
    return min(numer / denom, 1.0)


# ---------------------------------------------------------------------------
# Domain inference
# ---------------------------------------------------------------------------

def _infer_domain(text: str, skills: Iterable[str]) -> str:
    """
    Infer the most likely domain from free text + skills using keyword
    hit-counting against the domain keyword map.
    Returns an empty string when evidence is weak, which is safer than
    forcing a brittle domain assignment.
    """
    haystack = f"{clean_text(text)} {' '.join(clean_text(s) for s in skills)}".strip()
    if not haystack:
        return ""

    best_domain, best_hits, best_weight = "", 0, 0.0
    for domain, keywords in _domain_keyword_map().items():
        hits = 0
        weight = 0.0
        for kw in keywords:
            if not kw:
                continue
            pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
            if re.search(pattern, haystack):
                hits += 1
                weight += min(len(kw.split()) * 0.45 + len(kw) / 18.0, 2.0)
        if hits > best_hits or (hits == best_hits and weight > best_weight):
            best_domain, best_hits, best_weight = domain, hits, weight

    return best_domain if best_hits >= _MIN_DOMAIN_HITS else ""


# ---------------------------------------------------------------------------
# Role name normalisation  (for lookup / display)
# ---------------------------------------------------------------------------

def _normalize_role_name(role: str) -> str:
    """
    Map a user-supplied role string to the closest canonical role name
    using SequenceMatcher across role names and their aliases.
    """
    profiles = _load_role_profiles()
    target = clean_text(role)
    best_name: Optional[str] = None
    best_score = -1.0

    for _, row in profiles.iterrows():
        candidates = [row["role_clean"]] + row["aliases_list"]
        local_best = max(
            SequenceMatcher(None, target, opt).ratio() for opt in candidates
        )
        if local_best > best_score:
            best_name = row["Role"]
            best_score = local_best

    return best_name or role


# ---------------------------------------------------------------------------
# Softmax confidence calibration
# ---------------------------------------------------------------------------

def _softmax_percent(values: List[float]) -> List[float]:
    """
    Convert raw scores to calibrated confidence percentages via temperature-
    scaled softmax.  Temperature _SOFTMAX_TEMP controls spread:
    lower → sharper distinction, higher → softer / more uniform.
    """
    if not values:
        return []
    arr = np.array(values, dtype=float)
    # Shift for numerical stability
    arr = arr - arr.max()
    scaled = np.exp(arr * _SOFTMAX_TEMP)
    total = scaled.sum() or 1.0
    return [round(float(v / total) * 100, 2) for v in scaled]


# ---------------------------------------------------------------------------
# Input normalisation
# ---------------------------------------------------------------------------

def _build_input_payload(
    payload: Union[str, Dict[str, object]]
) -> Dict[str, object]:
    """
    Normalise any input format into a canonical dict with keys:
    text, skills, education, experience_years, domain.
    """
    if isinstance(payload, dict):
        text       = str(payload.get("text") or payload.get("Raw_Text") or "")
        skills     = payload.get("skills") or payload.get("Skills") or []
        education  = payload.get("education") or payload.get("Education") or []
        experience = payload.get("experience_years")
        if experience is None:
            experience = payload.get("Experience (Years)", 0)
        domain     = payload.get("domain") or payload.get("Domain") or ""
    else:
        text, skills, education, experience, domain = str(payload or ""), [], [], 0, ""

    if isinstance(skills, str):
        skills = _split_pipe_or_csv(skills)
    if isinstance(education, str):
        education = _split_pipe_or_csv(education)

    try:
        experience = float(experience or 0)
    except (TypeError, ValueError):
        experience = 0.0

    # Clean and alias-expand skills
    cleaned_skills = [clean_text(s) for s in skills if clean_text(s)]
    cleaned_skills = _expand_skill_aliases(cleaned_skills)

    return {
        "text":             clean_text(text),
        "skills":           cleaned_skills,
        "education":        [clean_text(e) for e in education if clean_text(e)],
        "experience_years": experience,
        "domain":           str(domain or "").strip(),
    }


# ---------------------------------------------------------------------------
# Core prediction engine
# ---------------------------------------------------------------------------

def predict_career(
    payload: Union[str, Dict[str, object]],
    top_k: int = 3,
    return_details: bool = False,
):
    """
    Predict the top-k most suitable career roles for a given profile.

    Parameters
    ----------
    payload : str | dict
        User profile. Accepted dict keys:
          text           – free-form description / bio
          skills         – list[str] or comma-separated string
          education      – list[str] or pipe/comma-separated string
          experience_years – numeric
          domain         – optional domain hint
    top_k : int
        Number of top predictions to return (default 3).
    return_details : bool
        If True, returns a rich dict with per-role breakdown.
        If False, returns list of (role_name_lower, confidence_pct).

    Returns
    -------
    list of (str, float)  –  when return_details=False
    dict                  –  when return_details=True
    """
    # ── 1. Load artefacts ──────────────────────────────────────────────────
    profiles = _load_role_profiles().copy()
    vf, mf, vs, ms = _role_vectorizer_bundle()
    idf_map = _skill_idf_map()

    # ── 2. Normalise input ──────────────────────────────────────────────────
    data = _build_input_payload(payload)
    user_skills_raw  = data["skills"]
    user_skills_exp  = _fuzzy_expand_skills(user_skills_raw)   # fuzzy-expanded
    user_edu         = data["education"]
    exp_years        = data["experience_years"]
    edu_rank         = _education_rank(user_edu)

    # ── 3. Domain inference ─────────────────────────────────────────────────
    inferred_domain = data["domain"] or _infer_domain(data["text"], user_skills_exp)

    # ── 4. Build query vectors ──────────────────────────────────────────────
    # Query for full-profile space
    full_query = " ".join(filter(None, [
        data["text"],
        " ".join(user_skills_exp * 2),   # double-weight skills in query
        " ".join(user_edu),
        clean_text(inferred_domain),
    ]))

    # Query for skills-only space
    skills_query = " ".join(user_skills_exp * 3)  # strongly weight skills

    if not full_query.strip() and not skills_query.strip():
        return [] if not return_details else {"top3": [], "predictions": []}

    q_full   = vf.transform([full_query])   if full_query.strip()   else None
    q_skills = vs.transform([skills_query]) if skills_query.strip() else None

    sim_full   = cosine_similarity(q_full,   mf)[0]   if q_full   is not None else np.zeros(len(profiles))
    sim_skills = cosine_similarity(q_skills, ms)[0]   if q_skills is not None else np.zeros(len(profiles))

    # ── 5. Per-role scoring ─────────────────────────────────────────────────
    detailed: List[Dict] = []

    for idx, row in profiles.iterrows():
        role_skills   = row["skills_list"]
        role_keywords = row["keywords_list"]

        # --- Skill IDF score (primary discriminator) ---
        skill_idf_score = _compute_skill_idf_score(
            user_skills_exp, role_skills, idf_map
        )
        # Also check against keywords (weaker signal, 0.4× weight)
        kw_idf_score = _compute_skill_idf_score(
            user_skills_exp, role_keywords, idf_map
        )
        combined_skill_idf = min(skill_idf_score + 0.4 * kw_idf_score, 1.0)

        # --- Experience score ---
        min_exp = float(row["Experience_Min"] or 0)
        max_exp = float(row["Experience_Max"] or max(min_exp + 1, 1))
        if exp_years < min_exp:
            # Under-qualified: gentle penalty
            gap = min_exp - exp_years
            exp_score = max(0.25, 1.0 - (gap / max(min_exp + 1, 1)) * 0.6)
        elif exp_years > max_exp:
            # Over-experienced: soft penalty (still plausible)
            excess = exp_years - max_exp
            exp_score = max(0.55, 1.0 - (excess / max(max_exp + 1, 1)) * 0.2)
        else:
            exp_score = 1.0

        # --- Education score ---
        role_edu_rank = _education_rank(row["education_list"])
        if edu_rank == 0 or role_edu_rank == 0:
            edu_score = 0.60
        elif edu_rank >= role_edu_rank:
            edu_score = 1.0
        else:
            # Under-qualified: scaled penalty
            edu_score = max(0.45, edu_rank / max(role_edu_rank, 1))

        # --- Domain / keyword contextual score ---
        domain_match  = (
            inferred_domain
            and clean_text(inferred_domain) == row["domain_clean"]
        )
        keyword_hits = 0
        for kw in role_keywords:
            if not kw:
                continue
            pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
            if re.search(pattern, full_query):
                keyword_hits += 1
        keyword_score = min(keyword_hits / max(len(role_keywords), 1), 1.0)
        domain_kw_score = max(
            1.0 if domain_match else (0.72 if not inferred_domain else 0.42),
            keyword_score,
        )

        # --- Evidence / coverage score ---
        matched_skill_ratio = len(set(user_skills_exp) & set(role_skills)) / max(len(set(role_skills)), 1)
        title_candidates = [row["role_clean"]] + row["aliases_list"]
        title_hit = 1.0 if any(tc and re.search(r"(?<!\w)" + re.escape(tc) + r"(?!\w)", full_query) for tc in title_candidates) else 0.0
        support_score = min(
            0.27 * float(sim_skills[idx])
            + 0.25 * combined_skill_idf
            + 0.14 * keyword_score
            + 0.12 * matched_skill_ratio
            + 0.22 * title_hit,
            1.0,
        )
        support_penalty = 1.0 if support_score >= _SUPPORT_FLOOR else max(0.72, 0.82 + support_score)

        # --- Weighted ensemble ---
        final_score = (
            _W_TFIDF_FULL   * float(sim_full[idx])
            + _W_TFIDF_SKILLS * float(sim_skills[idx])
            + _W_SKILL_IDF    * combined_skill_idf
            + _W_EDUCATION    * edu_score
            + _W_EXPERIENCE   * exp_score
            + _W_DOMAIN_KW    * domain_kw_score
            + 0.08            * title_hit
        ) * support_penalty

        detailed.append({
            "role":             row["Role"],
            "domain":           row["Domain"],
            "score":            round(float(final_score), 6),
            "similarity":       round(float(sim_full[idx]), 6),
            "skill_overlap":    round(float(skill_idf_score), 6),
            "education_score":  round(float(edu_score), 6),
            "experience_score": round(float(exp_score), 6),
            "domain_score":     round(float(domain_kw_score), 6),
            "matched_skills":   sorted(set(user_skills_exp) & set(role_skills)),
            "required_skills":  sorted(role_skills),
            "aliases":          row["aliases_list"],
            "support_score":    round(float(support_score), 6),
            "coverage_warning": support_score < _LOW_SUPPORT_THRESHOLD,
        })

    # ── 6. Sort + tie-breaking disambiguation ──────────────────────────────
    detailed.sort(key=lambda x: x["score"], reverse=True)

    # Resolve near-ties using keyword + alias text similarity as a tiebreaker
    _disambiguate(detailed, full_query, _TIEBREAK_BAND)

    top = detailed[: max(top_k, 1)]

    # ── 7. Confidence calibration ───────────────────────────────────────────
    all_confidences = _softmax_percent([x["score"] for x in detailed])
    confidence_map = {item["role"]: conf for item, conf in zip(detailed, all_confidences)}

    display_confidences: List[float] = []
    for idx, item in enumerate(top):
        raw_prob = confidence_map.get(item["role"], 0.0) / 100.0
        next_score = top[idx + 1]["score"] if idx + 1 < len(top) else top[idx]["score"]
        margin = max(item["score"] - next_score, 0.0) / max(top[0]["score"], 1e-6)
        display_conf = 100.0 * (
            0.50 * math.sqrt(max(raw_prob, 0.0))
            + 0.30 * item.get("support_score", 0.0)
            + 0.20 * min(margin * 3.0, 1.0)
        )
        if item.get("coverage_warning"):
            display_conf *= 0.78
        display_confidences.append(round(min(max(display_conf, 6.0), 96.0), 2))

    for idx in range(1, len(display_confidences)):
        if display_confidences[idx] > display_confidences[idx - 1]:
            display_confidences[idx] = max(6.0, round(display_confidences[idx - 1] - 0.5, 2))

    top3 = [(item["role"].lower(), conf) for item, conf in zip(top, display_confidences)]

    if return_details:
        for item, conf in zip(top, display_confidences):
            item["confidence"] = conf
            item["low_support"] = item.get("coverage_warning", False)
        return {
            "top3":             top3,
            "predictions":      top,
            "inferred_domain":  inferred_domain,
            "input_summary":    data,
        }

    return top3


# ---------------------------------------------------------------------------
# Tie-breaking disambiguation
# ---------------------------------------------------------------------------

def _role_description_text(row_data: Dict) -> str:
    """Reconstruct a role's description blob from a detailed result dict."""
    return " ".join(row_data.get("required_skills", []) + row_data.get("aliases", []))


def _disambiguate(
    detailed: List[Dict],
    query: str,
    band: float,
) -> None:
    """
    In-place re-rank of items within _TIEBREAK_BAND of each other.

    Two roles that are very close in ensemble score are re-ranked using
    a secondary score derived from:
      - SequenceMatcher similarity of query vs role description text
      - Number of rare (high-IDF) matched skills
    """
    if len(detailed) < 2:
        return

    idf_map = _skill_idf_map()
    top_score = detailed[0]["score"]
    band_end = 0
    for i, item in enumerate(detailed):
        if top_score - item["score"] <= band:
            band_end = i
        else:
            break

    if band_end < 1:
        return

    # Re-score items in the tie band
    def tiebreak_score(item: Dict) -> float:
        role_text = _role_description_text(item)
        text_sim = SequenceMatcher(None, query[:200], role_text[:200]).ratio()
        matched = item.get("matched_skills", [])
        rarity = sum(idf_map.get(sk, 1.0) for sk in matched)
        # Combine original score with tiebreak signals
        return item["score"] + 0.01 * text_sim + 0.005 * min(rarity / 5.0, 1.0)

    band_items = detailed[: band_end + 1]
    band_items.sort(key=tiebreak_score, reverse=True)
    detailed[: band_end + 1] = band_items


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    tests = [
        # 1. Classic ML Engineer
        {
            "text": "Python machine learning NLP transformers deep learning model deployment flask APIs",
            "skills": ["python", "machine learning", "deep learning", "nlp", "docker"],
            "education": ["btech computer science"],
            "experience_years": 2,
        },
        # 2. Frontend developer
        {
            "text": "Building responsive web apps with React and TypeScript",
            "skills": ["react", "typescript", "html", "css", "javascript", "figma"],
            "education": ["btech computer science"],
            "experience_years": 1,
        },
        # 3. Cybersecurity
        {
            "text": "SOC analyst with experience in SIEM, incident response, threat hunting",
            "skills": ["siem", "splunk", "incident response", "threat intelligence", "python"],
            "education": ["btech computer science", "cybersecurity"],
            "experience_years": 3,
        },
        # 4. Finance
        {
            "text": "financial modelling dcf valuation m&a equity research excel pitch decks",
            "skills": ["financial modeling", "excel", "dcf valuation", "equity research"],
            "education": ["mba finance"],
            "experience_years": 2,
        },
        # 5. GenAI / LLM
        {
            "text": "building RAG pipelines with LangChain and vector databases, fine-tuning LLMs",
            "skills": ["langchain", "rag", "vector databases", "prompt engineering", "python", "llm"],
            "education": ["mtech ai"],
            "experience_years": 2,
        },
    ]

    for i, sample in enumerate(tests, 1):
        result = predict_career(sample, return_details=True)
        print(f"\n{'='*60}")
        print(f"Test {i}: {sample['text'][:60]}...")
        print(f"Inferred domain: {result['inferred_domain']}")
        print("Top 3 predictions:")
        for role, conf in result["top3"]:
            print(f"  {role:40s}  {conf:5.1f}%")
