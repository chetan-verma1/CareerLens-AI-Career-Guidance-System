# CareerLens

CareerLens is a Flask-based career intelligence platform that analyzes resumes, predicts the most relevant career paths, estimates salary, evaluates ATS quality, and highlights skill gaps.

## Architecture

- `app.py` -> Flask routing layer
- `modules/resume_analyzer.py` -> PDF/DOCX text extraction, name/skill/education/experience extraction
- `modules/career_model.py` -> top-3 career prediction using TF-IDF similarity + skill overlap + education/experience scoring
- `modules/career_pipeline.py` -> orchestration for smart analyzer output
- `modules/career_skill.py` -> role skill gap analysis
- `modules/resume_ats.py` -> ATS and role-fit scoring
- `modules/salary_prediction.py` -> salary estimation model wrapper

## Data

Core prediction relies on:

- `data/career_role_profiles.csv`
- `data/career_skills.csv`
- `data/skills_data.csv`

These files are organized as role profiles, required skills, aliases, keywords, domain labels, and expected experience ranges. The goal is deterministic and realistic role matching rather than probabilistic classification over fake resume rows.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open:

- `http://127.0.0.1:5000/`

## Resume parsing behavior

Supported input:

- PDF
- DOCX

Analyzer output format:

```python
{
    "Name": "Candidate Name",
    "Skills": ["python", "sql", "machine learning"],
    "Experience (Years)": 2.5,
    "Education": ["btech computer science", "msc data science"],
    "Raw_Text": "..."
}
```

## Prediction logic

Career prediction is built from a weighted hybrid score:

- TF-IDF similarity between resume content and role profile text
- exact/fuzzy skill overlap
- education fit
- experience fit
- domain keyword alignment

Returned output includes:

- top 3 career predictions
- confidence percentages normalized across the top matches
- matched/missing skills
- ATS scores
- salary estimate payload

## Project size and deployment notes

Do **not** keep `venv/` inside the project folder.

Recommended production layout:

- project source in repo
- external virtual environment
- empty `uploads/` directory in repo
- models stored only if required for runtime

## Expanded role coverage

This version uses a curated occupation knowledge base with over 117 roles across 25 domains. The predictor matches resumes against structured role profiles instead of synthetic candidate rows.

### Role data grounding

The role taxonomy is curated from public occupational classification concepts and job-family structures inspired by O*NET, BLS SOC groups, and ESCO occupation-skill mappings. It is a curated knowledge base, not a labeled benchmark of real user resumes.
