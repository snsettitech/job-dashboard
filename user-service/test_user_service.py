#!/usr/bin/env python3
"""
Simple test script for User Service
Tests basic functionality without requiring a full test suite
"""

import requests
import json
import time
from typing import Dict, Any

class UserServiceTester:
    """Simple tester for User Service API"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_service_info(self) -> bool:
        """Test service information endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service info: {data.get('service')} v{data.get('version')}")
                return True
            else:
                print(f"❌ Service info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service info error: {e}")
            return False
    
    def test_user_registration(self, user_data: Dict[str, Any]) -> bool:
        """Test user registration"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User registration successful: {data.get('message')}")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ User registration error: {e}")
            return False
    
    def test_user_login(self, login_data: Dict[str, Any]) -> bool:
        """Test user login"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                print(f"✅ User login successful: {data.get('message')}")
                return True
            else:
                print(f"❌ User login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ User login error: {e}")
            return False
    
    def test_get_user_profile(self) -> bool:
        """Test getting user profile"""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{self.base_url}/api/v1/users/me",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User profile retrieved: {data.get('full_name')}")
                return True
            else:
                print(f"❌ Get user profile failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Get user profile error: {e}")
            return False
    
    def test_update_user_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Test updating user profile"""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.put(
                f"{self.base_url}/api/v1/users/me",
                json=profile_data,
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User profile updated: {data.get('full_name')}")
                return True
            else:
                print(f"❌ Update user profile failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Update user profile error: {e}")
            return False
    
    def test_token_refresh(self) -> bool:
        """Test token refresh"""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                print(f"✅ Token refresh successful")
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False
    
    def test_user_logout(self) -> bool:
        """Test user logout"""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/logout",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User logout successful: {data.get('message')}")
                return True
            else:
                print(f"❌ User logout failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ User logout error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting User Service Tests")
        print("=" * 50)
        
        # Test service health
        if not self.test_health_check():
            print("❌ Service is not healthy, stopping tests")
            return False
        
        if not self.test_service_info():
            print("❌ Service info failed, stopping tests")
            return False
        
        # Test user registration
        test_user = {
            "email": f"testuser{int(time.time())}@example.com",
            "username": f"testuser{int(time.time())}",
            "full_name": "Test User",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123"
        }
        
        if not self.test_user_registration(test_user):
            print("❌ User registration failed, stopping tests")
            return False
        
        # Test user login
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        if not self.test_user_login(login_data):
            print("❌ User login failed, stopping tests")
            return False
        
        # Test authenticated endpoints
        if not self.test_get_user_profile():
            print("❌ Get user profile failed")
            return False
        
        profile_update = {
            "full_name": "Updated Test User",
            "current_title": "Software Engineer",
            "location": "San Francisco, CA"
        }
        
        if not self.test_update_user_profile(profile_update):
            print("❌ Update user profile failed")
            return False
        
        # Test token refresh
        if not self.test_token_refresh():
            print("❌ Token refresh failed")
            return False
        
        # Test logout
        if not self.test_user_logout():
            print("❌ User logout failed")
            return False
        
        print("=" * 50)
        print("✅ All tests passed!")
        return True

def main():
    """Main test function"""
    print("🚀 User Service Test Runner")
    print("Make sure the user service is running on http://localhost:8001")
    print()
    
    # Wait a moment for user to read
    input("Press Enter to start tests...")
    
    tester = UserServiceTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("The user service is working correctly.")
    else:
        print("\n💥 Some tests failed!")
        print("Check the user service logs for more details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

