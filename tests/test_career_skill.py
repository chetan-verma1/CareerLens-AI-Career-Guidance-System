from modules.career_skill import skill_gap_analysis


def test_skill_gap_analysis_returns_expected_structure():
    matched, missing, score = skill_gap_analysis(
        ["python", "sql", "machine learning"],
        "Data Scientist"
    )

    assert isinstance(matched, list)
    assert isinstance(missing, list)
    assert isinstance(score, float)
    assert 0 <= score <= 100


def test_skill_gap_analysis_handles_invalid_career():
    matched, missing, score = skill_gap_analysis(
        ["python", "sql"],
        ""
    )

    assert matched == []
    assert isinstance(missing, list)
    assert score == 0.0