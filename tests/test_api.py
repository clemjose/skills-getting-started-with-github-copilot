"""
Test suite for Mergington High School API

Tests for all API endpoints using pytest with Arrange-Act-Assert pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset activities to initial state after each test."""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball league and practice",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["lucas@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis training and friendly matches",
            "schedule": "Wednesdays and Saturdays, 3:00 PM - 4:30 PM",
            "max_participants": 16,
            "participants": ["alex@mergington.edu", "jordan@mergington.edu"]
        },
        "Debate Club": {
            "description": "Develop critical thinking and public speaking skills",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["tara@mergington.edu"]
        },
        "Science Club": {
            "description": "Explore scientific concepts through experiments and discussions",
            "schedule": "Wednesdays, 3:30 PM - 4:30 PM",
            "max_participants": 25,
            "participants": ["noah@mergington.edu", "maya@mergington.edu"]
        },
        "Drama Club": {
            "description": "Stage performances, acting, and theatrical production",
            "schedule": "Mondays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["jasmine@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and visual art techniques",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["ava@mergington.edu", "connor@mergington.edu"]
        }
    }
    yield
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)


# ============================================================================
# GET /activities TESTS
# ============================================================================

class TestGetActivities:
    """Test suite for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities in the database."""
        # ARRANGE
        expected_activity_count = 9

        # ACT
        response = client.get("/activities")

        # ASSERT
        assert response.status_code == 200
        assert len(response.json()) == expected_activity_count
        assert "Chess Club" in response.json()
        assert "Programming Class" in response.json()

    def test_get_activities_returns_activity_structure(self, client, reset_activities):
        """Test that activities have the correct structure."""
        # ARRANGE
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # ACT
        response = client.get("/activities")
        activities_data = response.json()

        # ASSERT
        assert response.status_code == 200
        for activity in activities_data.values():
            assert all(field in activity for field in required_fields)

    def test_get_activities_chess_club_has_participants(self, client, reset_activities):
        """Test that Chess Club includes initial participants."""
        # ARRANGE
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

        # ACT
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]

        # ASSERT
        assert response.status_code == 200
        assert chess_club["participants"] == expected_participants


# ============================================================================
# POST /activities/{activity_name}/signup TESTS
# ============================================================================

class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_success(self, client, reset_activities):
        """Test successful signup of a new student for an activity."""
        # ARRANGE
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_student_fails(self, client, reset_activities):
        """Test that signing up a student already in the activity fails."""
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a non-existent activity fails."""
        # ARRANGE
        activity_name = "Fake Activity"
        email = "student@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities."""
        # ARRANGE
        email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class"]

        # ACT
        responses = []
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            responses.append(response)

        # ASSERT
        assert all(r.status_code == 200 for r in responses)
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


# ============================================================================
# DELETE /activities/{activity_name}/participants/{email} TESTS
# ============================================================================

class TestRemoveParticipant:
    """Test suite for DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_remove_existing_participant_success(self, client, reset_activities):
        """Test successful removal of a participant from an activity."""
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # ASSERT
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing a non-existent participant fails."""
        # ARRANGE
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # ASSERT
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that removing a participant from a non-existent activity fails."""
        # ARRANGE
        activity_name = "Fake Activity"
        email = "student@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_and_readd_participant(self, client, reset_activities):
        """Test that a removed participant can be re-added to the same activity."""
        # ARRANGE
        activity_name = "Tennis Club"
        email = "alex@mergington.edu"

        # ACT - Remove
        delete_response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # ACT - Re-add
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert delete_response.status_code == 200
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]


# ============================================================================
# ROOT ENDPOINT TESTS
# ============================================================================

class TestRootEndpoint:
    """Test suite for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Test that the root endpoint redirects to /static/index.html."""
        # ARRANGE
        # No specific arrangement needed

        # ACT
        response = client.get("/", follow_redirects=False)

        # ASSERT
        assert response.status_code == 307
        assert "/static/index.html" in response.headers.get("location", "")
