import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original)


def test_get_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Soccer Team" in payload
    assert "participants" in payload["Soccer Team"]


def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    response = client.post(
        f"/activities/Soccer%20Team/signup?email={email}"
    )

    assert response.status_code == 200
    assert email in activities["Soccer Team"]["participants"]


def test_unregister_removes_participant():
    email = "alex@mergington.edu"
    response = client.delete(
        f"/activities/Soccer%20Team/signup?email={email}"
    )

    assert response.status_code == 200
    assert email not in activities["Soccer Team"]["participants"]


def test_signup_duplicate_participant_returns_400():
    email = "alex@mergington.edu"
    response = client.post(
        f"/activities/Soccer%20Team/signup?email={email}"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_invalid_activity_returns_404():
    email = "newstudent@mergington.edu"
    response = client.post(
        f"/activities/Not%20A%20Club/signup?email={email}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up_returns_400():
    email = "newstudent@mergington.edu"
    response = client.delete(
        f"/activities/Soccer%20Team/signup?email={email}"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_invalid_activity_returns_404():
    email = "alex@mergington.edu"
    response = client.delete(
        f"/activities/Not%20A%20Club/signup?email={email}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
