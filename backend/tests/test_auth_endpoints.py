import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    # 1. Register a new user
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    print("\n1. Testing user registration...")
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json=register_data
    )
    print(f"Register response: {register_response.status_code}")
    print(register_response.json())

    # 2. Login and get token
    print("\n2. Testing login...")
    login_data = {
        "username": register_data["email"],  # OAuth2 expects 'username' not 'email'
        "password": register_data["password"],
        "grant_type": "password"  # Required for OAuth2
    }
    
    login_response = requests.post(
        f"{BASE_URL}/auth/token",
        data=login_data,  # Use data instead of json for form data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Login response: {login_response.status_code}")
    token_data = login_response.json()
    print(token_data)

    if login_response.status_code != 200:
        print("Login failed, stopping test")
        return

    # Set up headers with token
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }

    # 3. Test token validity
    print("\n3. Testing token validity...")
    test_token_response = requests.post(
        f"{BASE_URL}/auth/test-token",
        headers=headers
    )
    print(f"Test token response: {test_token_response.status_code}")
    print(test_token_response.json())

    if test_token_response.status_code != 200:
        print("Token validation failed, stopping test")
        return

    # 4. Start a session
    print("\n4. Testing session start...")
    session_response = requests.post(
        f"{BASE_URL}/api/sessions/start",
        headers=headers
    )
    print(f"Start session response: {session_response.status_code}")
    session_data = session_response.json()
    session_id = session_data["session_id"]
    print(session_data)

    # 5. Get session history
    print("\n5. Testing session history...")
    history_response = requests.get(
        f"{BASE_URL}/api/sessions/history",
        headers=headers
    )
    print(f"History response: {history_response.status_code}")
    print(json.dumps(history_response.json(), indent=2))

    # 6. End session
    print("\n6. Testing session end...")
    end_response = requests.post(
        f"{BASE_URL}/api/sessions/{session_id}/end",
        headers=headers
    )
    print(f"End session response: {end_response.status_code}")
    print(end_response.json())

    # 7. Get session recording
    print("\n7. Testing get recording...")
    recording_response = requests.get(
        f"{BASE_URL}/api/sessions/{session_id}/recording",
        headers=headers
    )
    print(f"Get recording response: {recording_response.status_code}")
    if recording_response.status_code == 200:
        recording_data = recording_response.json()
        print(f"Recording duration: {recording_data.get('duration')}")
        print(f"Frame count: {recording_data.get('frame_count')}")
    else:
        print(recording_response.json())

if __name__ == "__main__":
    test_auth_flow()