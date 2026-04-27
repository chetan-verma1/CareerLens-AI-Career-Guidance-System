from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Dict, Iterable, List, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def clean_text(text):
    if text is None or pd.isna(text):
        return ""
    text = str(text).lower().replace("c++", "cplusplus").replace("c#", "csharp").replace(".net", "dotnet")
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)
    return " ".join(text.split())


def _restore_skill(skill: str) -> str:
    return skill.replace("cplusplus", "c++").replace("csharp", "c#").replace("dotnet", ".net")


@lru_cache(maxsize=1)
def load_career_skills(path: str = "") -> Dict[str, List[str]]:
    csv_path = path or os.path.join(DATA_DIR, "career_skills.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    out: Dict[str, List[str]] = {}
    for _, row in df.iterrows():
        career = clean_text(row.get("Career", ""))
        skills = [clean_text(s) for s in re.split(r"[,|]", str(row.get("Skills", ""))) if clean_text(s)]
        if career:
            out[career] = list(dict.fromkeys(skills))
    return out


career_skills = load_career_skills()


def skill_gap_analysis(user_skills: Iterable[str], predicted_career: str) -> Tuple[List[str], List[str], float]:
    if not predicted_career or not career_skills:
        return [], ["Invalid Career/Database"], 0.0

    target = clean_text(predicted_career)
    match = process.extractOne(target, list(career_skills.keys()), scorer=fuzz.WRatio, score_cutoff=75)
    if not match:
        return [], [f"No skill data found for {predicted_career}"], 0.0

    resolved_career = match[0]
    required = career_skills[resolved_career]

    if isinstance(user_skills, str):
        users = [clean_text(s) for s in re.split(r"[,|]", user_skills) if clean_text(s)]
    else:
        users = [clean_text(s) for s in user_skills if clean_text(s)]

    matched, missing = [], []
    for req in required:
        res = process.extractOne(req, users, scorer=fuzz.token_set_ratio, score_cutoff=85)
        if res:
            matched.append(_restore_skill(req))
        else:
            missing.append(_restore_skill(req))

    score = round((len(matched) / max(len(required), 1)) * 100, 2)
    return matched, missing, score


if __name__ == "__main__":
    print(skill_gap_analysis(["python", "sql", "machine learning"], "Data Scientist"))
