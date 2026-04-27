from modules.career_model import predict_career


def test_career_model_returns_top_predictions():
    payload = {
        "text": "I have experience in Python, SQL, data analysis, dashboards and machine learning.",
        "skills": ["python", "sql", "data analysis", "machine learning"],
        "education": ["MCA"],
        "experience_years": 2,
        "domain": "Data Science & Analytics"
    }

    result = predict_career(payload, top_k=3)

    assert isinstance(result, list)
    assert len(result) > 0
    assert len(result) <= 3

    role, confidence = result[0]

    assert isinstance(role, str)
    assert isinstance(confidence, float)
    assert 0 <= confidence <= 100


def test_career_model_handles_empty_input():
    result = predict_career({}, top_k=3)

    assert result == []