"""
Quick API test script to verify backend functionality
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200


def test_register():
    """Test user registration"""
    print("\n2. Testing user registration...")

    # Random email to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"test_{timestamp}@example.com"

    data = {
        "email": email,
        "password": "SecurePass123",
        "name": "Test User",
        "date_of_birth": "1995-06-15",
        "gender": "male"
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"   Status: {response.status_code}")

    if response.status_code == 201:
        result = response.json()
        print(f"   User ID: {result['user_id']}")
        print(f"   Token: {result['access_token'][:50]}...")
        return result['access_token']
    else:
        print(f"   Error: {response.json()}")
        return None


def test_login():
    """Test user login"""
    print("\n3. Testing user login...")

    data = {
        "email": "user1@loveai.com",
        "password": "user123"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"   User ID: {result['user_id']}")
        print(f"   Role: {result['role']}")
        return result['access_token']
    else:
        print(f"   Error: {response.json()}")
        return None


def test_get_profile(token):
    """Test getting user profile"""
    print("\n4. Testing get profile...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/profiles/me", headers=headers)

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        profile = response.json()
        print(f"   Name: {profile['name']}")
        print(f"   Occupation: {profile.get('occupation', 'N/A')}")
        print(f"   Interests: {len(profile.get('interests', []))}")
        return True
    else:
        print(f"   Error: {response.json()}")
        return False


def test_get_discovery(token):
    """Test discovery endpoint"""
    print("\n5. Testing discovery (get profiles to swipe)...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/discovery/profiles?limit=5", headers=headers)

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        profiles = response.json()
        print(f"   Found {len(profiles)} profiles")
        if profiles:
            print(f"   First profile: {profiles[0]['name']}, {profiles[0]['age']} years old")
            if profiles[0].get('ai_compatibility_score'):
                print(f"   AI Compatibility: {profiles[0]['ai_compatibility_score']:.1f}%")
        return profiles
    else:
        print(f"   Error: {response.json()}")
        return []


def test_create_interaction(token, target_user_id):
    """Test creating interaction (like)"""
    print("\n6. Testing interaction (like)...")

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "to_user_id": target_user_id,
        "interaction_type": "like"
    }

    response = requests.post(f"{BASE_URL}/discovery/interact", json=data, headers=headers)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"   Is Match: {result['is_match']}")
        if result['is_match']:
            print(f"   Match ID: {result['match_id']}")
        return result
    else:
        print(f"   Error: {response.json()}")
        return None


def test_get_matches(token):
    """Test getting matches"""
    print("\n7. Testing get matches...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/discovery/matches", headers=headers)

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        matches = response.json()
        print(f"   Total matches: {len(matches)}")
        if matches:
            match = matches[0]
            print(f"   First match: {match['other_user_profile']['name']}")
            if match.get('ai_ice_breakers'):
                print(f"   Ice breakers: {len(match['ai_ice_breakers'])}")
        return matches
    else:
        print(f"   Error: {response.json()}")
        return []


def test_admin_stats(admin_token):
    """Test admin statistics"""
    print("\n8. Testing admin statistics...")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/admin/stats/users", headers=headers)

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        stats = response.json()
        print(f"   Total Users: {stats['total_users']}")
        print(f"   Active Users: {stats['active_users']}")
        print(f"   Total Matches: {stats['total_matches']}")
        print(f"   New Users Today: {stats['new_users_today']}")
        return True
    else:
        print(f"   Error: {response.json()}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("LoveAI Backend API Test Suite")
    print("=" * 60)

    # Test 1: Health check
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        return

    # Test 2: Register new user
    new_token = test_register()

    # Test 3: Login with demo user
    user_token = test_login()

    if not user_token:
        print("\n❌ Login failed. Run init_db.py to create demo users.")
        return

    # Test 4: Get profile
    test_get_profile(user_token)

    # Test 5: Get discovery profiles
    profiles = test_get_discovery(user_token)

    # Test 6: Create interaction
    if profiles:
        # Get the profile ID from the first profile
        target_user_id = profiles[0]['id']
        test_create_interaction(user_token, target_user_id)

    # Test 7: Get matches
    test_get_matches(user_token)

    # Test 8: Admin stats (with admin token)
    print("\n9. Testing admin login...")
    admin_data = {
        "email": "admin@loveai.com",
        "password": "admin123"
    }
    admin_response = requests.post(f"{BASE_URL}/auth/login", json=admin_data)
    if admin_response.status_code == 200:
        admin_token = admin_response.json()['access_token']
        test_admin_stats(admin_token)
    else:
        print("   ⚠️  Admin login failed. Run init_db.py to create admin user.")

    print("\n" + "=" * 60)
    print("✅ API Test Suite Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
