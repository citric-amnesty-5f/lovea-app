"""
Integration tests for complete user flows
"""
import pytest
from datetime import datetime


class TestCompleteUserFlow:
    """Test complete user journey from registration to matching"""

    def test_full_user_journey(self, client, db_session, sample_interests):
        """
        Test complete user flow:
        1. Register new user
        2. Login
        3. View and update profile
        4. Add interests and photos
        5. Set preferences
        6. Discover other profiles
        7. Like a profile and create match
        8. Logout
        9. Login again
        10. Verify session persists
        """

        # ==================== STEP 1: Register ====================
        print("\n=== Step 1: Register new user ===")
        register_response = client.post(
            "/auth/register",
            json={
                "email": "journey@example.com",
                "password": "SecurePass123",
                "name": "Journey User",
                "date_of_birth": "1995-06-15",
                "gender": "female"
            }
        )

        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "access_token" in register_data
        user_id = register_data["user_id"]
        first_token = register_data["access_token"]

        print(f"✓ User registered with ID: {user_id}")

        # ==================== STEP 2: Initial Login ====================
        print("\n=== Step 2: Login ===")
        login_response = client.post(
            "/auth/login",
            json={
                "email": "journey@example.com",
                "password": "SecurePass123"
            }
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print(f"✓ User logged in successfully")

        # ==================== STEP 3: View Profile ====================
        print("\n=== Step 3: View profile ===")
        profile_response = client.get("/profiles/me", headers=headers)

        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["name"] == "Journey User"
        assert profile_data["gender"] == "female"

        print(f"✓ Profile retrieved: {profile_data['name']}")

        # ==================== STEP 4: Update Profile ====================
        print("\n=== Step 4: Update profile ===")
        update_response = client.put(
            "/profiles/me",
            headers=headers,
            json={
                "bio": "Love hiking and photography!",
                "occupation": "Software Engineer",
                "location": "San Francisco, CA",
                "height": 165
            }
        )

        assert update_response.status_code == 200
        updated_profile = update_response.json()
        assert updated_profile["bio"] == "Love hiking and photography!"
        assert updated_profile["occupation"] == "Software Engineer"

        print(f"✓ Profile updated")

        # ==================== STEP 5: Add Interests ====================
        print("\n=== Step 5: Add interests ===")
        interest_ids = [i.id for i in sample_interests]
        interests_response = client.post(
            "/profiles/me/interests",
            headers=headers,
            json=interest_ids
        )

        assert interests_response.status_code == 200
        profile_with_interests = interests_response.json()
        assert len(profile_with_interests["interests"]) == 3

        print(f"✓ Added {len(profile_with_interests['interests'])} interests")

        # ==================== STEP 6: Add Photos ====================
        print("\n=== Step 6: Add photos ===")
        photo_response = client.post(
            "/profiles/me/photos",
            headers=headers,
            json={
                "url": "https://example.com/photo1.jpg",
                "order": 0,
                "is_primary": True
            }
        )

        assert photo_response.status_code == 200
        print(f"✓ Photo added")

        # ==================== STEP 7: Set Preferences ====================
        print("\n=== Step 7: Set dating preferences ===")
        prefs_response = client.put(
            "/profiles/me/preferences",
            headers=headers,
            json={
                "min_age": 25,
                "max_age": 35,
                "looking_for": ["male"],
                "max_distance": 50
            }
        )

        assert prefs_response.status_code == 200
        print(f"✓ Preferences set: ages 25-35, looking for males")

        # ==================== STEP 8: Complete Onboarding ====================
        print("\n=== Step 8: Complete onboarding ===")
        onboarding_response = client.post(
            "/profiles/complete-onboarding",
            headers=headers
        )

        assert onboarding_response.status_code == 200
        print(f"✓ Onboarding completed")

        # ==================== STEP 9: Create Another User to Match With ====================
        print("\n=== Step 9: Create potential match ===")
        # Create another user to match with
        from app.models import User, Profile, Preference, Gender
        from app.auth import get_password_hash

        match_user = User(
            email="match@example.com",
            password_hash=get_password_hash("MatchPass123"),
            role="user"
        )
        db_session.add(match_user)
        db_session.flush()

        match_profile = Profile(
            user_id=match_user.id,
            name="Match User",
            date_of_birth=datetime(1992, 3, 20),
            gender=Gender.MALE,
            bio="Looking for adventure",
            onboarding_completed=True,
            profile_completion=80
        )
        db_session.add(match_profile)
        db_session.flush()

        match_prefs = Preference(
            profile_id=match_profile.id,
            min_age=22,
            max_age=35,
            looking_for=["female"],
            max_distance=50
        )
        db_session.add(match_prefs)
        db_session.commit()

        print(f"✓ Created potential match: {match_profile.name}")

        # ==================== STEP 10: Discovery ====================
        print("\n=== Step 10: Discover profiles ===")
        discovery_response = client.get(
            "/discovery/profiles?limit=5",
            headers=headers
        )

        assert discovery_response.status_code == 200
        profiles = discovery_response.json()
        assert len(profiles) > 0

        print(f"✓ Found {len(profiles)} profiles to browse")

        # ==================== STEP 11: Like Profile ====================
        print("\n=== Step 11: Like a profile ===")
        target_profile = profiles[0]
        like_response = client.post(
            "/discovery/interact",
            headers=headers,
            json={
                "to_user_id": target_profile["id"],
                "interaction_type": "like"
            }
        )

        assert like_response.status_code == 200
        like_data = like_response.json()
        print(f"✓ Liked profile: {target_profile['name']}")
        print(f"  Is match: {like_data['is_match']}")

        # ==================== STEP 12: Like Back to Create Match ====================
        print("\n=== Step 12: Create mutual match ===")
        # Login as match user and like back
        match_login_response = client.post(
            "/auth/login",
            json={
                "email": "match@example.com",
                "password": "MatchPass123"
            }
        )
        match_token = match_login_response.json()["access_token"]
        match_headers = {"Authorization": f"Bearer {match_token}"}

        # Like back
        like_back_response = client.post(
            "/discovery/interact",
            headers=match_headers,
            json={
                "to_user_id": user_id,
                "interaction_type": "like"
            }
        )

        assert like_back_response.status_code == 200
        mutual_like_data = like_back_response.json()
        assert mutual_like_data["is_match"] is True
        match_id = mutual_like_data["match_id"]

        print(f"✓ Mutual match created! Match ID: {match_id}")

        # ==================== STEP 13: View Matches ====================
        print("\n=== Step 13: View matches ===")
        matches_response = client.get(
            "/discovery/matches",
            headers=headers
        )

        assert matches_response.status_code == 200
        matches = matches_response.json()
        assert len(matches) >= 1

        print(f"✓ Total matches: {len(matches)}")

        # ==================== STEP 14: Send Message ====================
        print("\n=== Step 14: Send message ===")
        message_response = client.post(
            "/messages/",
            headers=headers,
            json={
                "match_id": match_id,
                "content": "Hey! Nice to match with you!"
            }
        )

        assert message_response.status_code == 201
        print(f"✓ Message sent")

        # ==================== STEP 15: View Conversations ====================
        print("\n=== Step 15: View conversations ===")
        conversations_response = client.get(
            "/messages/conversations",
            headers=headers
        )

        assert conversations_response.status_code == 200
        conversations = conversations_response.json()
        assert len(conversations) >= 1

        print(f"✓ Conversations: {len(conversations)}")

        # ==================== STEP 16: Logout ====================
        print("\n=== Step 16: Logout ===")
        logout_response = client.post(
            "/auth/logout",
            headers=headers
        )

        assert logout_response.status_code == 200
        print(f"✓ Logged out successfully")

        # ==================== STEP 17: Login Again ====================
        print("\n=== Step 17: Login again ===")
        relogin_response = client.post(
            "/auth/login",
            json={
                "email": "journey@example.com",
                "password": "SecurePass123"
            }
        )

        assert relogin_response.status_code == 200
        new_token = relogin_response.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        print(f"✓ Logged in again successfully")

        # ==================== STEP 18: Verify Data Persists ====================
        print("\n=== Step 18: Verify data persists ===")
        # Check profile still has all data
        final_profile_response = client.get(
            "/profiles/me",
            headers=new_headers
        )

        assert final_profile_response.status_code == 200
        final_profile = final_profile_response.json()
        assert final_profile["bio"] == "Love hiking and photography!"
        assert len(final_profile["interests"]) == 3
        assert final_profile["onboarding_completed"] is True

        # Check matches still exist
        final_matches_response = client.get(
            "/discovery/matches",
            headers=new_headers
        )
        assert len(final_matches_response.json()) >= 1

        print(f"✓ All data persisted correctly")

        # ==================== SUCCESS ====================
        print("\n" + "=" * 60)
        print("✅ COMPLETE USER JOURNEY TEST PASSED!")
        print("=" * 60)
        print(f"User ID: {user_id}")
        print(f"Profile: {final_profile['name']}")
        print(f"Interests: {len(final_profile['interests'])}")
        print(f"Matches: {len(final_matches_response.json())}")
        print("=" * 60)


class TestAuthenticationFlow:
    """Test authentication flow edge cases"""

    def test_register_login_logout_login_cycle(self, client):
        """Test full auth cycle"""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "cycle@example.com",
                "password": "CyclePass123",
                "name": "Cycle User",
                "date_of_birth": "1995-01-01",
                "gender": "male"
            }
        )
        assert register_response.status_code == 201

        # Login
        login1 = client.post(
            "/auth/login",
            json={
                "email": "cycle@example.com",
                "password": "CyclePass123"
            }
        )
        token1 = login1.json()["access_token"]
        assert login1.status_code == 200

        # Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert logout_response.status_code == 200

        # Login again
        login2 = client.post(
            "/auth/login",
            json={
                "email": "cycle@example.com",
                "password": "CyclePass123"
            }
        )
        token2 = login2.json()["access_token"]
        assert login2.status_code == 200
        assert token1 != token2  # New token generated

        # Verify new token works
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response.status_code == 200
