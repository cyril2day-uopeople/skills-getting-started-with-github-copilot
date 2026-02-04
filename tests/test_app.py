"""
Tests for the Mergington High School API application.

Tests cover the main endpoints:
- GET /activities - returns all activities
- POST /activities/{activity_name}/signup - signup a student for an activity
- POST /activities/{activity_name}/unregister - unregister a student from an activity
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI application."""
    return TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify we have all expected activities
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        assert "Basketball" in activities
        assert "Tennis Club" in activities
        assert "Art Studio" in activities
        assert "Drama Club" in activities
        assert "Debate Team" in activities
        assert "Science Club" in activities
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has the required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_have_participants(self, client):
        """Test that activities have initial participants."""
        response = client.get("/activities")
        activities = response.json()
        
        # Check that at least one activity has participants
        has_participants = any(len(activity["participants"]) > 0 for activity in activities.values())
        assert has_participants


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_student(self, client):
        """Test that a new student can sign up for an activity."""
        response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_to_nonexistent_activity(self, client):
        """Test that signing up for a non-existent activity returns 404."""
        response = client.post("/activities/Nonexistent Club/signup?email=student@mergington.edu")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_duplicate_signup(self, client):
        """Test that a student cannot sign up twice for the same activity."""
        # First signup
        response1 = client.post("/activities/Chess Club/signup?email=duplicate@mergington.edu")
        assert response1.status_code == 200
        
        # Try to sign up again
        response2 = client.post("/activities/Chess Club/signup?email=duplicate@mergington.edu")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_to_full_activity(self, client):
        """Test that signing up for a full activity returns 400."""
        # Create an activity with max 1 participant by filling it up
        # We'll test with an activity that has limited capacity
        # First, verify activity capacity and fill it
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Find an activity with available slots
        activity_name = "Science Club"
        
        # Signup multiple students until activity is full
        initial_count = len(activities[activity_name]["participants"])
        max_participants = activities[activity_name]["max_participants"]
        
        # Signup students until full
        for i in range(max_participants - initial_count):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Try to sign up one more (should be full)
        response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")
        assert response.status_code == 400
        assert "full" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_existing_student(self, client):
        """Test that a registered student can unregister from an activity."""
        # First, get current state
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Find an activity with participants
        activity_name = None
        student_email = None
        for name, activity in activities.items():
            if activity["participants"]:
                activity_name = name
                student_email = activity["participants"][0]
                break
        
        if activity_name and student_email:
            # Unregister the student
            response = client.post(f"/activities/{activity_name}/unregister?email={student_email}")
            assert response.status_code == 200
            assert "Unregistered" in response.json()["message"]
            
            # Verify the student was removed
            activities_response = client.get("/activities")
            activities = activities_response.json()
            assert student_email not in activities[activity_name]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test that unregistering from non-existent activity returns 404."""
        response = client.post("/activities/Nonexistent Club/unregister?email=student@mergington.edu")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_unregister_unregistered_student(self, client):
        """Test that unregistering a non-registered student returns 400."""
        response = client.post("/activities/Chess Club/unregister?email=notregistered@mergington.edu")
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_signup_after_unregister(self, client):
        """Test that a student can sign up after unregistering."""
        email = "signup_unregister@mergington.edu"
        activity_name = "Tennis Club"
        
        # First signup
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.post(f"/activities/{activity_name}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response3.status_code == 200
