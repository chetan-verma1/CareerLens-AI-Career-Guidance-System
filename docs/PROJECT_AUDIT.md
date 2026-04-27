# CareerLens Project Audit and Technical Summary

## 1. Project Overview

CareerLens is a hybrid AI and machine-learning-based career guidance system. It analyzes resumes, extracts skills, recommends suitable career roles, identifies missing skills, predicts salary, and checks resume ATS compatibility.

The project is suitable for MCA final-year submission because it combines web development, machine learning, NLP-style resume processing, data analysis, testing, and software engineering practices.

---

## 2. Main Modules

| Module | File | Purpose |
|---|---|---|
| Resume Analyzer | `modules/resume_analyzer.py` | Extracts text, skills, education, experience, and candidate details from resumes |
| Career Recommendation | `modules/career_model.py` | Predicts suitable career roles using hybrid similarity scoring |
| Skill Gap Analysis | `modules/career_skill.py` | Compares user skills with required skills for a target role |
| Salary Prediction | `modules/salary_prediction.py` | Predicts expected salary using a regression model |
| ATS Checker | `modules/resume_ats.py` | Generates general and role-specific ATS scores |
| Smart Pipeline | `modules/career_pipeline.py` | Combines all modules into a complete career analysis workflow |
| Flask App | `app.py` | Handles routes, APIs, UI rendering, and file upload processing |

---

## 3. AI / ML Techniques Used

### Resume Analysis

Techniques used:

- PDF/DOCX text extraction
- Rule-based NLP
- Regular expressions
- Section detection
- Skill dictionary matching
- Fuzzy matching using RapidFuzz

### Career Recommendation

Techniques used:

- TF-IDF vectorization
- Cosine similarity
- Skill overlap scoring
- Education matching
- Experience matching
- Domain matching
- Weighted ranking

The output score represents a career match score, not classification accuracy.

### Skill Gap Analysis

Techniques used:

- Set comparison
- Required skill matching
- Missing skill identification
- Readiness score calculation

### Salary Prediction

Techniques used:

- Linear Regression
- OneHotEncoder
- Scikit-learn Pipeline
- Joblib model loading

### ATS Scoring

Techniques used:

- Rule-based scoring
- Keyword matching
- Structure analysis
- Skill depth analysis
- Impact statement analysis
- Role-specific matching

---

## 4. System Pipeline

```text
Resume Upload
    ↓
Secure File Validation
    ↓
Text Extraction
    ↓
Resume Data Extraction
    ↓
Career Recommendation
    ↓
Skill Gap Analysis
    ↓
Salary Prediction
    ↓
ATS Score Calculation
    ↓
Dashboard Result