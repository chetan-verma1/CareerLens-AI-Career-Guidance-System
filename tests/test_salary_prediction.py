from modules.salary_prediction import predict_salary


def test_salary_prediction_returns_valid_response():
    result = predict_salary(
        role="Data Analyst",
        experience_years=2,
        domain="Data Science & Analytics",
        state="Punjab"
    )

    assert isinstance(result, dict)
    assert "predicted_lpa" in result
    assert "display_text" in result
    assert result["predicted_lpa"] >= 0
    assert result["currency"] == "INR"


def test_salary_prediction_handles_invalid_experience():
    result = predict_salary(
        role="Software Engineer",
        experience_years="invalid",
        domain="Software Engineering",
        state="Punjab"
    )

    assert isinstance(result, dict)
    assert result["experience_years"] == 0.0
    assert result["predicted_lpa"] >= 0