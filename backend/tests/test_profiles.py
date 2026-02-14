"""
Tests for profile management endpoints
"""
import pytest


class TestProfileRetrieval:
    """Test getting profiles"""

    def test_get_own_profile(self, client, auth_headers):
        """Test getting own profile"""
        response = client.get("/profiles/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test User"
        assert data["gender"] == "male"
        assert "preferences" in data

    def test_get_profile_by_id(self, client, auth_headers, test_user):
        """Test getting profile by user ID"""
        response = client.get(
            f"/profiles/{test_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test User"

    def test_get_profile_without_auth(self, client):
        """Test getting profile without authentication"""
        response = client.get("/profiles/me")

        assert response.status_code == 401


class TestProfileUpdate:
    """Test updating profiles"""

    def test_update_profile(self, client, auth_headers):
        """Test updating own profile"""
        response = client.put(
            "/profiles/me",
            headers=auth_headers,
            json={
                "bio": "Updated bio",
                "occupation": "Software Engineer",
                "location": "San Francisco, CA"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio"
        assert data["occupation"] == "Software Engineer"
        assert data["location"] == "San Francisco, CA"

    def test_update_profile_completion(self, client, auth_headers):
        """Test that profile completion is calculated"""
        # Initial state
        response = client.get("/profiles/me", headers=auth_headers)
        initial_completion = response.json()["profile_completion"]

        # Update with more info
        client.put(
            "/profiles/me",
            headers=auth_headers,
            json={
                "bio": "A detailed bio about myself",
                "occupation": "Engineer",
                "location": "San Francisco"
            }
        )

        # Check updated completion
        response = client.get("/profiles/me", headers=auth_headers)
        new_completion = response.json()["profile_completion"]

        assert new_completion > initial_completion


class TestInterests:
    """Test interest management"""

    def test_get_all_interests(self, client, sample_interests):
        """Test getting all available interests"""
        response = client.get("/profiles/interests/all")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert any(i["name"] == "Hiking" for i in data)

    def test_add_interests(self, client, auth_headers, sample_interests):
        """Test adding interests to profile"""
        interest_ids = [i.id for i in sample_interests]

        response = client.post(
            "/profiles/me/interests",
            headers=auth_headers,
            json=interest_ids
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["interests"]) == 3

    def test_remove_interest(self, client, auth_headers, sample_interests):
        """Test removing interest from profile"""
        # First add interests
        interest_ids = [i.id for i in sample_interests]
        client.post(
            "/profiles/me/interests",
            headers=auth_headers,
            json=interest_ids
        )

        # Then remove one
        response = client.delete(
            f"/profiles/me/interests/{sample_interests[0].id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["interests"]) == 2


class TestPhotos:
    """Test photo management"""

    def test_add_photo(self, client, auth_headers):
        """Test adding photo to profile"""
        response = client.post(
            "/profiles/me/photos",
            headers=auth_headers,
            json={
                "url": "https://example.com/photo.jpg",
                "order": 0,
                "is_primary": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/photo.jpg"
        assert data["is_primary"] is True

    def test_delete_photo(self, client, auth_headers):
        """Test deleting photo"""
        # First add a photo
        add_response = client.post(
            "/profiles/me/photos",
            headers=auth_headers,
            json={
                "url": "https://example.com/photo.jpg",
                "order": 0,
                "is_primary": True
            }
        )
        photo_id = add_response.json()["id"]

        # Then delete it
        response = client.delete(
            f"/profiles/me/photos/{photo_id}",
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_photo_limit(self, client, auth_headers):
        """Test that photo limit (6) is enforced"""
        # Add 6 photos
        for i in range(6):
            client.post(
                "/profiles/me/photos",
                headers=auth_headers,
                json={
                    "url": f"https://example.com/photo{i}.jpg",
                    "order": i
                }
            )

        # Try to add 7th photo
        response = client.post(
            "/profiles/me/photos",
            headers=auth_headers,
            json={
                "url": "https://example.com/photo7.jpg",
                "order": 7
            }
        )

        assert response.status_code == 400
        assert "Maximum" in response.json()["detail"]


class TestPreferences:
    """Test dating preferences"""

    def test_get_preferences(self, client, auth_headers):
        """Test getting preferences"""
        response = client.get(
            "/profiles/me/preferences",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "min_age" in data
        assert "max_age" in data
        assert "looking_for" in data

    def test_update_preferences(self, client, auth_headers):
        """Test updating preferences"""
        response = client.put(
            "/profiles/me/preferences",
            headers=auth_headers,
            json={
                "min_age": 25,
                "max_age": 40,
                "looking_for": ["female"],
                "max_distance": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["min_age"] == 25
        assert data["max_age"] == 40
        assert data["max_distance"] == 100

    def test_invalid_age_range(self, client, auth_headers):
        """Test that max_age must be >= min_age"""
        response = client.put(
            "/profiles/me/preferences",
            headers=auth_headers,
            json={
                "min_age": 40,
                "max_age": 25  # Invalid: less than min_age
            }
        )

        assert response.status_code == 422

    def test_invalid_age_range_with_partial_update(self, client, auth_headers):
        """Test partial updates can't create invalid min/max age combinations."""
        set_max_response = client.put(
            "/profiles/me/preferences",
            headers=auth_headers,
            json={"max_age": 30}
        )
        assert set_max_response.status_code == 200

        response = client.put(
            "/profiles/me/preferences",
            headers=auth_headers,
            json={"min_age": 35}
        )

        assert response.status_code == 422


class TestOnboarding:
    """Test onboarding flow"""

    def test_complete_onboarding(self, client, auth_headers):
        """Test completing onboarding"""
        response = client.post(
            "/profiles/complete-onboarding",
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify it's marked as complete
        profile_response = client.get("/profiles/me", headers=auth_headers)
        assert profile_response.json()["onboarding_completed"] is True
