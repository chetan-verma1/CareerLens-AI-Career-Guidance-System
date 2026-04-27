from app import app


def test_landing_page_loads():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200


def test_explore_page_loads():
    client = app.test_client()
    response = client.get("/explore")

    assert response.status_code == 200


def test_main_app_page_loads():
    client = app.test_client()
    response = client.get("/app")

    assert response.status_code == 200


def test_meta_options_api_returns_data():
    client = app.test_client()
    response = client.get("/meta/options")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, dict)
    assert "roles" in data
    assert "domains" in data
    assert "states" in data
    assert "skills" in data


def test_career_model_rejects_empty_input():
    client = app.test_client()
    response = client.post("/career_model", json={})

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data


def test_career_skill_rejects_empty_input():
    client = app.test_client()
    response = client.post("/career_skill", json={})

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data


def test_salary_prediction_rejects_empty_input():
    client = app.test_client()
    response = client.post("/salary_prediction", json={})

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data