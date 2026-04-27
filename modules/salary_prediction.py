from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict

STATE_MULTIPLIERS = {
    "karnataka": 1.10, "maharashtra": 1.08, "telangana": 1.07, "delhi": 1.06, "tamil nadu": 1.03,
    "haryana": 1.03, "gujarat": 1.02, "west bengal": 0.98, "kerala": 0.98, "uttar pradesh": 0.96,
    "rajasthan": 0.95, "madhya pradesh": 0.94, "odisha": 0.93, "bihar": 0.91, "assam": 0.92,
}

DOMAIN_MULTIPLIERS = {
    "software engineering": 1.10, "data science & analytics": 1.12, "artificial intelligence": 1.18,
    "cloud & infrastructure": 1.14, "cybersecurity": 1.15, "product & project management": 1.08,
    "finance & accounting": 1.02, "sales": 1.01, "marketing": 1.00, "education & research": 0.94,
    "operations & supply chain": 0.97, "healthcare": 1.00,
}

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "salary_model.pkl")
DATA_PATH = os.path.join(DATA_DIR, "salary_data.csv")


@lru_cache(maxsize=1)
def _load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def predict_salary(role: str, experience_years: float = 0, domain: str = "", state: str = "") -> Dict[str, object]:
    model = _load_model()
    try:
        experience_years = float(experience_years or 0)
    except (TypeError, ValueError):
        experience_years = 0.0

    if model is None:
        return {
            "role": role,
            "experience_years": experience_years,
            "predicted_lpa": 0.0,
            "currency": "INR",
            "display_text": "Salary estimate unavailable",
            "note": "Salary model unavailable.",
        }

    input_df = pd.DataFrame([[role, experience_years]], columns=["Role", "Experience_Years"])
    predicted_salary = float(model.predict(input_df)[0])

    state_factor = STATE_MULTIPLIERS.get(str(state or "").strip().lower(), 1.0)
    domain_factor = DOMAIN_MULTIPLIERS.get(str(domain or "").strip().lower(), 1.0)
    predicted_salary = round(max(predicted_salary * state_factor * domain_factor, 0.0), 2)
    return {
        "role": role,
        "experience_years": experience_years,
        "predicted_lpa": predicted_salary,
        "currency": "INR",
        "domain": domain,
        "state": state,
        "display_text": f"₹{predicted_salary:.2f} LPA",
        "note": f"Estimated for {role} at {experience_years:g} years of experience" + (f" in {state}" if state else "") + (f" within {domain}" if domain else "") + ".",
    }


if __name__ == "__main__":
    print("Training Salary Prediction Model...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    X = df[["Role", "Experience_Years"]]
    y = df["Salary_LPA"]
    preprocessor = ColumnTransformer(
        transformers=[("role_enc", OneHotEncoder(handle_unknown="ignore"), ["Role"])],
        remainder="passthrough",
    )
    salary_model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression()),
    ])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    salary_model.fit(X_train, y_train)
    joblib.dump(salary_model, MODEL_PATH)
    print("Salary prediction model saved ✅")
