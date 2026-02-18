import copy
from urllib.parse import quote

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


def test_signup_invalid_email_returns_400():
    """Test that invalid email format returns 400"""
    invalid_emails = [
        "notanemail",
        "missing@domain",
        "@nodomain.com",
        "spaces in@email.com",
        "toolong" + "a" * 250 + "@domain.com",
        "user..name@domain.com",  # consecutive dots
        ".user@domain.com",  # leading dot
        "user.@domain.com",  # trailing dot
        "user@.domain.com",  # leading dot in domain
        "user@domain..com",  # consecutive dots in domain
    ]
    
    for email in invalid_emails:
        # URL encode the email to handle special characters
        encoded_email = quote(email, safe='')
        response = client.post(
            f"/activities/Soccer%20Team/signup?email={encoded_email}"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid email format"


def test_unregister_invalid_email_returns_400():
    """Test that invalid email format returns 400 for unregister"""
    email = "notanemail"
    # URL encode the email to handle special characters
    encoded_email = quote(email, safe='')
    response = client.delete(
        f"/activities/Soccer%20Team/signup?email={encoded_email}"
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email format"


def test_signup_at_capacity_returns_400():
    """Test that signup fails when activity is at max capacity"""
    # Get current state of Chess Club
    response = client.get("/activities")
    chess_club = response.json()["Chess Club"]
    current_participants = len(chess_club["participants"])
    max_participants = chess_club["max_participants"]
    
    # Calculate how many spots are available
    spots_available = max_participants - current_participants
    
    # Fill the activity to capacity
    for i in range(spots_available):
        email = f"student{i}@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 200
    
    # Try to add one more student when at capacity
    email = "overflow@mergington.edu"
    response = client.post(
        f"/activities/Chess%20Club/signup?email={email}"
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is at maximum capacity"


def test_signup_with_plus_sign_email():
    """Test that emails with plus signs (for aliasing) are accepted"""
    valid_emails_with_plus = [
        "user+tag@mergington.edu",
        "student+filter@example.com",
    ]
    
    for email in valid_emails_with_plus:
        # URL encode the email to handle special characters like +
        encoded_email = quote(email, safe='')
        response = client.post(
            f"/activities/Art%20Club/signup?email={encoded_email}"
        )
        assert response.status_code == 200
        assert email in activities["Art Club"]["participants"]
