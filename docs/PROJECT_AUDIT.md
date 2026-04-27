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

## 5. Backend Review

The backend is developed using Flask and provides routes for:

Landing page
Explore page
Main application dashboard
Career prediction API
Skill gap API
Salary prediction API
ATS resume checker API
Metadata options API

Backend improvements completed:

Secure upload validation
PDF/DOCX file restriction
5 MB upload size limit
UUID-based temporary filenames
Uploaded file cleanup after processing
Debug mode controlled using environment variable

---

## 6. UI Review

The UI includes:

Landing page
Explore page
Smart analyzer dashboard
Resume analyzer tool
Career predictor tool
Skill gap tool
Salary predictor tool
ATS checker tool

UI improvements completed:

Removed career match percentage from dashboard role cards
Kept ATS score percentages where meaningful
Improved wording from prediction confidence to career match quality

---

## 7. Testing Summary

The project includes a pytest-based test suite.

Test files:

Test File	Purpose
tests/test_career_model.py	Tests career recommendation output and empty input handling
tests/test_career_skill.py	Tests skill gap analysis output structure
tests/test_salary_prediction.py	Tests salary prediction response and invalid experience handling

Current result:

6 passed

---


## 8. Salary Model Evaluation

The salary model was evaluated using:

python evaluation/evaluate_salary_model.py

Evaluation result:

Total records: 3488
Test records: 698
MAE: 0.53 LPA
RMSE: 0.62 LPA
R2 Score: 0.9854

This shows that the salary prediction model performs well on the available dataset.

---

## 9. Strengths

Clear real-world problem
Modular architecture
Multiple AI/ML-inspired tools
Resume parsing support
Career recommendation system
Skill gap analysis
Salary prediction
ATS scoring
Web-based interface
GitHub version control
Test suite included
Model evaluation included
Secure file upload handling
Clean repository structure
Report-ready documentation

---


## 10. Current Scope and Future Enhancements

CareerLens has been developed as a complete academic prototype that successfully implements resume analysis, career recommendation, skill gap analysis, salary prediction, ATS scoring, testing, and model evaluation. The current version focuses on explainable AI/ML techniques and a modular web-based architecture.

The following points define the current scope of the system and provide opportunities for future enhancement:

The career recommendation module currently uses a hybrid scoring approach based on TF-IDF vectorization, cosine similarity, skill matching, education, experience, and domain relevance. This approach provides explainable recommendations. In future, transformer-based models such as BERT can be integrated for deeper semantic understanding.
The resume analysis module uses rule-based NLP, regular expressions, section detection, and fuzzy skill matching to extract information from resumes. This makes the system transparent and lightweight. Future versions can include advanced NER-based extraction and OCR support for scanned resumes.
The ATS scoring module evaluates resume structure, keyword strength, skills, impact, education, experience, and role relevance. It is designed as an ATS-inspired academic scoring system. Future versions can include more industry-specific resume scoring templates.
The salary prediction module uses a regression-based machine learning model trained on the available salary dataset. Future versions can include additional features such as city, company type, certification level, job demand, and real-time market data.
The current version focuses on individual career analysis. Future enhancements can include user login, saved career reports, admin dashboard, cloud deployment, and PDF report export.

These enhancements can further improve the scalability, intelligence, and industry applicability of the system while the current version already satisfies the core objectives of the project.


---

## 11. Final Technical Verdict

CareerLens is feasible and suitable for MCA final-year project submission. It demonstrates practical use of Python, Flask, machine learning, NLP-style text processing, data analysis, testing, and secure software development practices.

The project should be described as a hybrid AI and ML-based career guidance system rather than a pure deep learning or LLM-based system.

---