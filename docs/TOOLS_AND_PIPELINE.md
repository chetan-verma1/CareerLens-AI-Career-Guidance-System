# CareerLens Tools and Pipeline Manual

## Main user-facing flows

### 1. Smart Resume Analyzer
Route flow:

`app.py` -> `run_pipeline()` -> `analyze_resume()` -> `predict_career()` -> `skill_gap_analysis()` / ATS / salary

Returned payload includes:

- name
- top 3 roles
- best career
- confidence
- ATS score
- matched skills
- missing skills
- salary details
- suggestions

### 2. Resume Analyzer Tool
Route flow:

`app.py` -> `analyze_resume()`

Purpose:

- extract raw text
- detect name
- detect skills
- estimate experience
- detect education

### 3. Career Model API
Route flow:

`/career_model` -> `predict_career(text or structured payload)`

Current behavior:

- accepts raw text compatibility path
- internally builds a role-match score against the curated role profile dataset
- returns top 3 predictions

## Resume Analyzer internals

### Text extraction order

1. `pdfplumber` for native PDF text
2. `pypdf` fallback for PDFs
3. optional OCR fallback only if optional OCR libraries are available
4. `python-docx` for DOCX

### Extraction stages

1. normalize text
2. split resume into sections
3. extract candidate name from top lines or email fallback
4. extract skills using exact lexicon matching + fuzzy resolution
5. extract education using degree patterns and education section content
6. estimate experience from explicit years or date ranges

## Career Model internals

### Dataset

`data/career_role_profiles.csv`

Each role stores:

- role title
- domain
- aliases
- role description
- required skills
- education hints
- min/max experience
- role keywords

### Scoring

Final score is a weighted combination of:

- semantic similarity over TF-IDF profile text
- skill overlap
- education suitability
- experience suitability
- domain/keyword alignment

### Confidence

Confidence is normalized only over the top returned roles so the UI gets stable percentages.

## How to extend roles

Add a row to `data/career_role_profiles.csv` with:

- `Role`
- `Domain`
- `Aliases`
- `Description`
- `Skills`
- `Education`
- `Experience_Min`
- `Experience_Max`
- `Keywords`

Then mirror/update:

- `data/career_skills.csv`
- `data/skills_data.csv`

## Notes for production

- keep uploaded resumes outside version control
- log extraction errors per file type
- add offline evaluation with labeled resume-role ground truth
- add country-specific salary/role datasets when scaling beyond baseline support


## Expanded ontology

- Domains: 25
- Roles: 117
- Career matching uses role-profile retrieval with TF-IDF similarity plus explicit skill, education, and experience scoring.
- Skill-gap analysis reads required skills directly from the expanded role database.
