# CareerLens: AI-Based Career Guidance and Skill Gap Analysis System

CareerLens is a hybrid AI and machine-learning-based career guidance platform developed as an MCA final-year project. It analyzes user resumes, extracts skills, recommends suitable career roles, identifies missing skills, estimates salary ranges, and evaluates resume ATS compatibility.

The system is built using Python, Flask, Scikit-learn, rule-based NLP, TF-IDF vectorization, cosine similarity, fuzzy matching, and regression-based salary prediction.

---

## Project Overview

Students and early professionals often face difficulty in choosing a suitable career path because of changing industry requirements, lack of personalized guidance, and limited awareness of required skills.

CareerLens solves this problem by providing an integrated career intelligence platform that offers:

- Resume analysis
- Career recommendation
- Skill gap analysis
- Salary prediction
- ATS resume scoring
- Smart analyzer dashboard

---

## Key Features

### 1. Smart Resume Analyzer

Uploads a resume and generates a complete career analysis report.

It includes:

- Extracted candidate details
- Top career recommendations
- Skill gap analysis
- ATS score
- Salary estimate
- Personalized improvement suggestions

### 2. Resume Analyzer

Extracts structured information from PDF and DOCX resumes.

Extracted fields include:

- Name
- Skills
- Education
- Experience
- Raw resume text

### 3. Career Recommendation System

Recommends suitable career roles using a hybrid matching approach.

Techniques used:

- TF-IDF vectorization
- Cosine similarity
- Skill overlap scoring
- Education matching
- Experience matching
- Domain matching
- Weighted ranking

### 4. Skill Gap Analysis

Compares user skills with required skills for a target career role.

Output includes:

- Matched skills
- Missing skills
- Readiness score

### 5. Salary Prediction

Predicts expected salary in LPA based on role and experience.

Techniques used:

- Linear Regression
- OneHotEncoder
- Scikit-learn Pipeline
- Joblib model loading

### 6. ATS Resume Checker

Evaluates resume quality using an ATS-inspired scoring system.

It checks:

- Resume structure
- Keyword strength
- Skill depth
- Impact statements
- Education information
- Experience information
- Role-specific relevance

---

## Tech Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| Frontend | HTML, CSS, JavaScript |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas, NumPy |
| Resume Parsing | pdfplumber, pypdf, python-docx |
| Fuzzy Matching | RapidFuzz |
| Model Storage | Joblib |
| Testing | Pytest |
| Version Control | Git and GitHub |

---

## AI / ML Modules Used

| Module | File | Techniques Used |
|---|---|---|
| Resume Analysis | `modules/resume_analyzer.py` | Rule-based NLP, regex, fuzzy matching, PDF/DOCX text extraction |
| Career Recommendation | `modules/career_model.py` | TF-IDF, cosine similarity, weighted scoring |
| Skill Gap Analysis | `modules/career_skill.py` | Set matching, skill comparison |
| Salary Prediction | `modules/salary_prediction.py` | Linear Regression, OneHotEncoder, Scikit-learn Pipeline |
| ATS Scoring | `modules/resume_ats.py` | Rule-based scoring, keyword analysis |
| Smart Pipeline | `modules/career_pipeline.py` | Integrated multi-module workflow |

---

## Project Structure

```text
CareerLens/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── career_role_profiles.csv
│   ├── career_skills.csv
│   ├── jobs.csv
│   ├── salary_data.csv
│   ├── skill_catalog.csv
│   └── skills_data.csv
│
├── docs/
│   └── TOOLS_AND_PIPELINE.md
│
├── evaluation/
│   └── evaluate_salary_model.py
│
├── model/
│   └── salary_model.pkl
│
├── modules/
│   ├── career_model.py
│   ├── career_pipeline.py
│   ├── career_skill.py
│   ├── resume_analyzer.py
│   ├── resume_ats.py
│   ├── salary_prediction.py
│   └── skill_db.py
│
├── static/
│   ├── css/
│   ├── images/
│   └── js/
│
├── templates/
│   ├── index.html
│   ├── landing.html
│   └── explore.html
│
├── tests/
│   ├── test_career_model.py
│   ├── test_career_skill.py
│   └── test_salary_prediction.py
│
└── uploads/
    └── .gitkeep