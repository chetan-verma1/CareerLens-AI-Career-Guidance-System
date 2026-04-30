# PROJECT_EXPLANATION.md

# CareerLens: Project Explanation

## 1. Why I Built CareerLens

I built CareerLens to help students, fresh graduates, and early professionals make better career decisions using resume-based analysis and AI/ML techniques.

Many students have technical skills, projects, and academic knowledge, but they are often confused about:

- which career role suits their profile,
- which skills are missing for a target role,
- whether their resume is ready for screening,
- what salary range they can expect,
- and how to improve their profile for placements or job applications.

CareerLens was developed as an academic AI/ML-based career guidance system that converts a resume or skill profile into useful career insights.

---

## 2. Main Problem It Solves

Career planning is usually scattered across many different sources. A student may use one website for jobs, another for salary information, another for resume checking, and another for learning skills. This creates confusion and does not provide a complete profile-based view.

CareerLens solves this problem by combining multiple career guidance features in one platform:

- Resume analysis
- Career role recommendation
- Skill gap analysis
- Salary prediction
- ATS-inspired resume scoring
- Personalized improvement suggestions

The main goal is to provide a single, structured, and explainable career guidance dashboard for students and early professionals.

---

## 3. System Architecture

CareerLens follows a modular Flask-based web application architecture.

### High-Level Flow

```text
User Interface
HTML / CSS / JavaScript
        ↓
Flask Backend
Routes, APIs, file upload, validation
        ↓
Processing Modules
Resume analysis, career prediction, skill gap, salary, ATS
        ↓
Data Layer
CSV datasets and saved ML model
        ↓
Dashboard Output
Career matches, missing skills, salary estimate, ATS score, suggestions
```

### Main Layers

| Layer | Purpose |
|---|---|
| Frontend Layer | Provides pages, forms, dashboard, buttons, upload fields, and result sections |
| Flask Backend Layer | Handles routes, APIs, file uploads, validation, and template rendering |
| Processing Layer | Runs Python modules for resume analysis, recommendation, skill gap, salary, and ATS scoring |
| Data Layer | Stores role, skill, job, and salary data in CSV files |
| Model Layer | Stores the trained salary prediction model as `salary_model.pkl` |
| Testing Layer | Uses pytest to validate backend routes and module logic |

---

## 4. Modules and Their Purpose

### 4.1 `app.py`

This is the main Flask application file. It connects the frontend with backend logic.

Purpose:

- Defines routes for pages and tools
- Handles resume uploads
- Calls backend modules
- Returns output to the dashboard
- Handles API requests and validation

---

### 4.2 `modules/resume_analyzer.py`

This module extracts useful information from PDF and DOCX resumes.

Purpose:

- Extract resume text
- Identify candidate details
- Extract skills
- Detect education information
- Estimate experience
- Return structured resume data

Techniques used:

- PDF/DOCX text extraction
- Rule-based NLP
- Regular expressions
- Section detection
- Skill dictionary matching
- Fuzzy matching
- OCR fallback for scanned resumes

---

### 4.3 `modules/career_model.py`

This module recommends suitable career roles based on user resume/profile.

Purpose:

- Compare user skills and resume text with career role profiles
- Generate top career recommendations
- Calculate confidence scores
- Apply weighted ranking

Techniques used:

- TF-IDF vectorization
- Cosine similarity
- Skill overlap scoring
- Education matching
- Experience matching
- Domain keyword matching
- Weighted recommendation ranking

---

### 4.4 `modules/career_skill.py`

This module performs skill gap analysis.

Purpose:

- Compare user skills with required skills for a selected role
- Find matched skills
- Find missing skills
- Calculate readiness score

Example:

```text
Required skills: Python, SQL, Excel, Power BI
User skills: Python, SQL
Matched skills: Python, SQL
Missing skills: Excel, Power BI
```

---

### 4.5 `modules/salary_prediction.py`

This module predicts an estimated salary range.

Purpose:

- Load trained salary model
- Accept inputs such as role, domain, state, and experience
- Predict estimated salary in LPA

Techniques used:

- Regression-based machine learning
- Encoded categorical features
- Scikit-learn pipeline
- Joblib model loading

Important note:

The salary output is an estimate based on available dataset patterns. It is not a guaranteed salary.

---

### 4.6 `modules/resume_ats.py`

This module evaluates resume quality using ATS-inspired scoring.

Purpose:

- Check resume structure
- Check keyword strength
- Check skill depth
- Check education and experience details
- Check role-specific relevance
- Generate ATS score and feedback

Important note:

This is ATS-inspired scoring. It does not claim to replicate any real proprietary ATS software.

---

### 4.7 `modules/career_pipeline.py`

This module connects all major tools into one Smart Analyzer pipeline.

Purpose:

- Analyze uploaded resume
- Predict top career roles
- Run skill gap analysis
- Predict salary
- Calculate general and role-specific ATS score
- Generate improvement suggestions
- Return final dashboard-ready output

---

### 4.8 `modules/skill_db.py`

This module supports skill-related operations.

Purpose:

- Load skill data
- Provide skill suggestions
- Support skill matching and frontend dropdown/search features

---

## 5. Technologies Used

| Category | Technology / Library | Purpose |
|---|---|---|
| Programming Language | Python | Main backend and ML logic |
| Web Framework | Flask | Routes, APIs, file upload, backend processing |
| Frontend | HTML, CSS, JavaScript | UI, dashboard, forms, buttons, dynamic interaction |
| Data Handling | pandas | Reading and processing CSV datasets |
| Numerical Processing | NumPy | Numerical operations and ML support |
| Machine Learning | scikit-learn | TF-IDF, similarity, regression, preprocessing, evaluation |
| Fuzzy Matching | RapidFuzz | Matching similar skill names and spelling variations |
| PDF Parsing | pdfplumber, pypdf | Extracting text from PDF resumes |
| DOCX Parsing | python-docx | Extracting text from DOCX resumes |
| OCR | pytesseract, pdf2image, Pillow | Extracting text from scanned/image-based resumes |
| Model Storage | joblib | Loading saved salary prediction model |
| Testing | pytest | Automated module and route testing |
| Version Control | Git and GitHub | Tracking project changes and maintaining repository |

---

## 6. ML/NLP Logic

CareerLens uses a hybrid AI/ML approach. This means it does not depend on only one model. Different techniques are used for different modules according to their purpose.

### 6.1 Resume Parsing Logic

Resume parsing uses rule-based NLP and document extraction.

Steps:

1. User uploads PDF or DOCX resume.
2. System extracts text using PDF/DOCX libraries.
3. If the resume is scanned, OCR is used as fallback.
4. Extracted text is cleaned and normalized.
5. Skills, education, and experience are detected using rules, regex, skill catalog, and fuzzy matching.

Simple explanation:

The system reads the resume, cleans the text, searches for important sections, and converts unstructured resume content into structured data.

---

### 6.2 TF-IDF Vectorization

TF-IDF stands for Term Frequency-Inverse Document Frequency.

It converts text into numerical vectors so that the computer can compare resume text with career role profiles.

Purpose in CareerLens:

- Convert resume/profile text into numbers
- Convert career role descriptions into numbers
- Help identify which role is most similar to the user profile

Simple explanation:

TF-IDF gives more importance to meaningful words like `Python`, `SQL`, `Machine Learning`, and less importance to common words like `the`, `and`, or `work`.

---

### 6.3 Cosine Similarity

Cosine similarity measures how similar two text vectors are.

Purpose in CareerLens:

- Compare user resume/profile vector with each career role vector
- Give higher score to roles that are more similar to the user profile

Simple explanation:

If the user resume has skills close to a Data Analyst role, then the Data Analyst role receives a higher similarity score.

---

### 6.4 Skill Overlap Scoring

Skill overlap scoring compares user skills with required role skills.

Purpose:

- Count matched skills
- Count missing skills
- Estimate readiness for a role

Simple explanation:

If a role requires 10 skills and the user has 6 of them, the system understands that the user is partially ready and still needs 4 skills.

---

### 6.5 Fuzzy Skill Matching

Fuzzy matching handles spelling variations and similar words.

Example:

```text
JavaScript ≈ javascript
Machine Learning ≈ machin learning
PostgreSQL ≈ Postgres
```

Purpose in CareerLens:

- Improve skill extraction
- Handle spelling differences
- Match abbreviations or variations

---

### 6.6 Weighted Ranking

Career recommendation does not depend on only one factor. It combines multiple scores.

Factors used:

- TF-IDF text similarity
- Skill match score
- Education match
- Experience match
- Domain keyword match

Simple explanation:

The system gives marks for different factors and combines them to produce the final career recommendation score.

---

### 6.7 Regression-Based Salary Prediction

Regression is a machine learning method used to predict numerical values.

Purpose in CareerLens:

- Predict estimated salary based on role, domain, state, and experience

Simple explanation:

The model learns salary patterns from previous salary data and predicts an estimated salary for the user’s selected role and experience.

---

### 6.8 ATS-Inspired Rule-Based Scoring

The ATS checker uses rules to evaluate resume quality.

It checks:

- Resume sections
- Skills
- Keywords
- Education
- Experience
- Project impact
- Role-specific relevance

Simple explanation:

It checks whether the resume looks job-ready and gives suggestions for improvement.

---

## 7. Challenges Faced

### 7.1 Unstructured Resume Formats

Resumes can have different layouts, headings, fonts, and writing styles. This makes extraction difficult.

Handling approach:

- Used PDF/DOCX parsing
- Used section detection
- Used regex and rule-based extraction
- Used fuzzy matching for skills

---

### 7.2 Skill Name Variations

The same skill can be written in different ways.

Examples:

- `JS` and `JavaScript`
- `ML` and `Machine Learning`
- `PowerBI` and `Power BI`

Handling approach:

- Used aliases
- Used normalized text
- Used fuzzy matching

---

### 7.3 Scanned Resumes

Some PDFs may contain images instead of selectable text.

Handling approach:

- Added OCR support using Tesseract-based pipeline

---

### 7.4 Recommendation Accuracy

Career recommendation depends on role data, skill mapping, and resume quality.

Handling approach:

- Used multiple scoring factors instead of one algorithm
- Combined similarity, skill match, education, experience, and domain signals

---

### 7.5 Salary Prediction Reliability

Salary varies by company, location, market trend, role level, and candidate strength.

Handling approach:

- Used regression model for academic estimation
- Clearly treated output as an estimated salary, not guaranteed salary

---

### 7.6 Frontend and Backend Integration

Multiple tools had to work inside one dashboard.

Handling approach:

- Used Flask routes and APIs
- Used JavaScript for dynamic section switching and result display
- Used modular backend code

---

## 8. Limitations

CareerLens is a strong academic prototype, but it has some limitations.

- Salary prediction depends on the available salary dataset.
- ATS score is rule-based and inspired by ATS concepts, not an actual proprietary ATS.
- Resume parsing accuracy depends on resume formatting and text quality.
- Scanned resumes require OCR tools to be installed correctly.
- The system currently does not use login or user profile storage.
- It does not use real-time job market APIs.
- It does not use transformer-based deep learning models such as BERT.
- The dataset is curated for academic demonstration and can be expanded.
- The system is currently more suitable for student and fresher-level guidance.

---

## 9. Future Improvements

The project can be improved further in the following ways:

- Add user login and saved career reports
- Add admin dashboard for managing roles, skills, and datasets
- Add real-time job market API integration
- Add real-time salary data from trusted job platforms
- Add PDF report export
- Add cloud deployment
- Add email-based report sharing
- Add advanced NLP or transformer models for deeper resume understanding
- Add course recommendations for missing skills
- Add interview question generation based on target role
- Add more datasets for better salary and career prediction accuracy
- Add analytics dashboard for training institutes

---

## 10. What I Learned

During this project, I learned how to build a complete AI/ML-based web application from idea to implementation.

### Technical Learning

- How to build a Flask web application
- How frontend and backend communicate
- How to handle file uploads securely
- How to extract text from PDF and DOCX resumes
- How OCR works for scanned documents
- How to use pandas for CSV data processing
- How to use scikit-learn for TF-IDF and regression
- How cosine similarity works for recommendation
- How fuzzy matching improves skill extraction
- How to save and load ML models using Joblib
- How to write pytest test cases
- How to use Git and GitHub for version control

### Project Development Learning

- How to divide a project into modules
- How to design a dashboard-style UI
- How to connect multiple tools into one smart pipeline
- How to validate user input
- How to handle errors and invalid files
- How to document a project professionally
- How to prepare a project for viva, interviews, and future improvements

### Personal Learning

This project helped me understand how AI/ML can be applied to real-world career guidance problems. I learned that a useful AI system is not only about one model. It also requires data preparation, backend logic, frontend design, testing, security, documentation, and clear explanation.

---

## Final Summary

CareerLens is a hybrid AI/ML-based career guidance system that helps users analyze resumes, identify suitable career roles, find missing skills, estimate salary, and improve resume readiness. It uses a combination of machine learning, NLP-style text processing, fuzzy matching, rule-based scoring, and web development. The project is explainable, modular, and suitable for academic evaluation, interviews, and future enhancement.
