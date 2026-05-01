import copy
import pathlib
import sys
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.app import activities, app

INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app)


def activity_url(activity_name: str, suffix: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}{suffix}"


def test_get_activities_returns_expected_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert expected_activity in data
    assert data[expected_activity]["max_participants"] == 12
    assert data[expected_activity]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_new_email_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        activity_url(activity_name, "/signup"), params={"email": new_email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in activities[activity_name]["participants"]


def test_signup_duplicate_email_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(
        activity_url(activity_name, "/signup"), params={"email": existing_email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert len(activities[activity_name]["participants"]) == initial_count


def test_remove_participant_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = "michael@mergington.edu"

    # Act
    response = client.delete(
        activity_url(activity_name, "/participants"), params={"email": email_to_remove}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email_to_remove} from {activity_name}"
    assert email_to_remove not in activities[activity_name]["participants"]


def test_remove_missing_participant_returns_404(client):
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missing@mergington.edu"

    # Act
    response = client.delete(
        activity_url(activity_name, "/participants"), params={"email": missing_email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"
