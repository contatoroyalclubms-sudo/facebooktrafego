import requests
import json

def test_authentication():
    """Testar autenticação completa"""
    base_url = "http://localhost:8000"
    
    print("1. Testando health check...")
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n2. Testando login...")
    login_data = {
        "username": "admin@metaads.com",
        "password": "admin123"
    }
    
    response = requests.post(
        f"{base_url}/api/v1/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        token = result["access_token"]
        
        print(f"✅ Login successful!")
        print(f"Token: {token[:50]}...")
        
        print("\n3. Testando rota /me...")
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
        
        print(f"Status: {me_response.status_code}")
        if me_response.status_code == 200:
            user_data = me_response.json()
            print(f"✅ /me successful!")
            print(f"User ID: {user_data['id']}")
            print(f"Email: {user_data['email']}")
            print(f"Full Name: {user_data['full_name']}")
            print(f"Is Active: {user_data['is_active']}")
        else:
            print(f"❌ /me failed: {me_response.text}")
    else:
        print(f"❌ Login failed: {response.text}")

if __name__ == "__main__":
    test_authentication()
