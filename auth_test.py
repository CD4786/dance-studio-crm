#!/usr/bin/env python3
"""
Authentication System Testing for Mobile Login Issues
Testing Objectives:
1. Authentication API Testing
2. Mobile-Specific Authentication Issues  
3. User Account Verification
4. Error Handling Analysis
"""

import requests
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class AuthenticationTester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.user_info = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = f"{status} {name} {details}"
        print(result)
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, 
                    expected_status: int = 200, headers: Dict[str, str] = None) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        if headers:
            request_headers.update(headers)
        
        if self.token:
            request_headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            if not success:
                print(f"   ⚠️  Status: {response.status_code}, Expected: {expected_status}")
                print(f"   📄 Response: {response_data}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   🔥 Request failed: {str(e)}")
            return False, {"error": str(e)}

    def test_admin_user_exists(self):
        """Test if admin user exists in database by attempting login"""
        print("\n🔍 TESTING: Admin User Account Verification")
        
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.admin_token = response.get('access_token')
            self.user_info = response.get('user', {})
            user_role = self.user_info.get('role', 'Unknown')
            user_name = self.user_info.get('name', 'Unknown')
            user_active = self.user_info.get('is_active', False)
            
            print(f"   👤 Admin User: {user_name}")
            print(f"   🎭 Role: {user_role}")
            print(f"   ✅ Active: {user_active}")
            print(f"   🔑 Token Length: {len(self.admin_token) if self.admin_token else 0} chars")
            
            # Verify admin has proper permissions
            has_admin_role = user_role in ['owner', 'manager', 'admin']
            account_active = user_active is True
            
            success = success and has_admin_role and account_active
            
        self.log_test("Admin User Account Verification", success, 
                     f"- User: {self.user_info.get('name', 'Unknown')}, Role: {self.user_info.get('role', 'Unknown')}")
        return success

    def test_login_api_structure(self):
        """Test login API response structure and token generation"""
        print("\n🔍 TESTING: Login API Response Structure")
        
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            # Check required response fields
            required_fields = ['access_token', 'token_type', 'user']
            missing_fields = []
            
            for field in required_fields:
                if field not in response:
                    missing_fields.append(field)
                    success = False
            
            # Check user object structure
            user_obj = response.get('user', {})
            required_user_fields = ['id', 'email', 'name', 'role', 'is_active']
            missing_user_fields = []
            
            for field in required_user_fields:
                if field not in user_obj:
                    missing_user_fields.append(field)
                    success = False
            
            # Check token format (JWT should have 3 parts separated by dots)
            token = response.get('access_token', '')
            token_parts = token.split('.') if token else []
            valid_jwt_format = len(token_parts) == 3
            
            if not valid_jwt_format:
                success = False
            
            print(f"   📋 Response Fields: {list(response.keys())}")
            print(f"   👤 User Fields: {list(user_obj.keys())}")
            print(f"   🔑 Token Format: {'Valid JWT' if valid_jwt_format else 'Invalid JWT'}")
            
            if missing_fields:
                print(f"   ❌ Missing Response Fields: {missing_fields}")
            if missing_user_fields:
                print(f"   ❌ Missing User Fields: {missing_user_fields}")
                
        self.log_test("Login API Response Structure", success, 
                     f"- JWT Format: {'Valid' if valid_jwt_format else 'Invalid'}")
        return success

    def test_token_validation(self):
        """Test JWT token validation with protected endpoints"""
        print("\n🔍 TESTING: Token Validation")
        
        if not self.admin_token:
            self.log_test("Token Validation", False, "- No admin token available")
            return False
        
        # Test accessing protected endpoint with valid token
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.make_request('GET', 'students', expected_status=200)
        
        if success:
            students_count = len(response) if isinstance(response, list) else 0
            print(f"   📊 Protected endpoint accessible: {students_count} students found")
        
        # Restore original token
        self.token = original_token
        
        self.log_test("Token Validation", success, 
                     f"- Protected endpoint accessible with valid token")
        return success

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        print("\n🔍 TESTING: Invalid Credentials Handling")
        
        test_cases = [
            {
                "name": "Wrong Password",
                "email": "admin@test.com",
                "password": "wrongpassword",
                "expected_status": 401
            },
            {
                "name": "Non-existent User",
                "email": "nonexistent@test.com", 
                "password": "admin123",
                "expected_status": 401
            },
            {
                "name": "Empty Email",
                "email": "",
                "password": "admin123",
                "expected_status": 422
            },
            {
                "name": "Empty Password",
                "email": "admin@test.com",
                "password": "",
                "expected_status": 422
            }
        ]
        
        successful_tests = 0
        
        for test_case in test_cases:
            login_data = {
                "email": test_case["email"],
                "password": test_case["password"]
            }
            
            success, response = self.make_request('POST', 'auth/login', login_data, 
                                                test_case["expected_status"])
            
            if success:
                successful_tests += 1
                print(f"   ✅ {test_case['name']}: Correctly returned {test_case['expected_status']}")
            else:
                print(f"   ❌ {test_case['name']}: Expected {test_case['expected_status']}")
        
        overall_success = successful_tests == len(test_cases)
        self.log_test("Invalid Credentials Handling", overall_success, 
                     f"- {successful_tests}/{len(test_cases)} error scenarios handled correctly")
        return overall_success

    def test_invalid_token_handling(self):
        """Test handling of invalid/expired tokens"""
        print("\n🔍 TESTING: Invalid Token Handling")
        
        test_cases = [
            {
                "name": "Invalid Token Format",
                "token": "invalid.token.here",
                "expected_status": 401
            },
            {
                "name": "Empty Token",
                "token": "",
                "expected_status": 401
            },
            {
                "name": "Malformed JWT",
                "token": "not.a.valid.jwt.token",
                "expected_status": 401
            }
        ]
        
        successful_tests = 0
        
        for test_case in test_cases:
            # Save current token
            original_token = self.token
            
            # Set test token
            self.token = test_case["token"]
            
            # Try to access protected endpoint
            success, response = self.make_request('GET', 'students', 
                                                expected_status=test_case["expected_status"])
            
            # Restore original token
            self.token = original_token
            
            if success:
                successful_tests += 1
                print(f"   ✅ {test_case['name']}: Correctly returned {test_case['expected_status']}")
            else:
                print(f"   ❌ {test_case['name']}: Expected {test_case['expected_status']}")
        
        overall_success = successful_tests == len(test_cases)
        self.log_test("Invalid Token Handling", overall_success, 
                     f"- {successful_tests}/{len(test_cases)} invalid token scenarios handled correctly")
        return overall_success

    def test_cors_headers(self):
        """Test CORS headers for mobile browser compatibility"""
        print("\n🔍 TESTING: CORS Headers for Mobile Compatibility")
        
        # Test preflight request (OPTIONS)
        url = f"{self.api_url}/auth/login"
        headers = {
            'Origin': 'https://studio-manager-5.preview.emergentagent.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        
        try:
            response = requests.options(url, headers=headers, timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            print(f"   🌐 CORS Headers Found:")
            for header, value in cors_headers.items():
                if value:
                    print(f"      {header}: {value}")
                else:
                    print(f"      {header}: Not Set")
            
            # Check if essential CORS headers are present
            has_origin = cors_headers['Access-Control-Allow-Origin'] is not None
            has_methods = cors_headers['Access-Control-Allow-Methods'] is not None
            has_headers = cors_headers['Access-Control-Allow-Headers'] is not None
            
            success = has_origin and has_methods and has_headers
            
        except Exception as e:
            print(f"   🔥 CORS test failed: {str(e)}")
            success = False
            cors_headers = {}
        
        self.log_test("CORS Headers for Mobile Compatibility", success, 
                     f"- Essential headers present: {success}")
        return success

    def test_mobile_user_agent_login(self):
        """Test login with mobile user agent strings"""
        print("\n🔍 TESTING: Mobile User Agent Compatibility")
        
        mobile_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        ]
        
        successful_logins = 0
        
        for i, user_agent in enumerate(mobile_user_agents):
            device_type = ["iPhone", "Android", "iPad"][i]
            
            headers = {
                'User-Agent': user_agent,
                'Content-Type': 'application/json'
            }
            
            login_data = {
                "email": "admin@test.com",
                "password": "admin123"
            }
            
            success, response = self.make_request('POST', 'auth/login', login_data, 200, headers)
            
            if success:
                successful_logins += 1
                token = response.get('access_token', '')
                print(f"   ✅ {device_type}: Login successful, token length: {len(token)}")
            else:
                print(f"   ❌ {device_type}: Login failed")
        
        overall_success = successful_logins == len(mobile_user_agents)
        self.log_test("Mobile User Agent Compatibility", overall_success, 
                     f"- {successful_logins}/{len(mobile_user_agents)} mobile devices supported")
        return overall_success

    def test_session_persistence(self):
        """Test session/token persistence across requests"""
        print("\n🔍 TESTING: Session/Token Persistence")
        
        if not self.admin_token:
            self.log_test("Session/Token Persistence", False, "- No admin token available")
            return False
        
        # Make multiple requests with the same token
        self.token = self.admin_token
        
        endpoints_to_test = [
            ('students', 'GET'),
            ('teachers', 'GET'),
            ('enrollments', 'GET'),
            ('dashboard/stats', 'GET')
        ]
        
        successful_requests = 0
        
        for endpoint, method in endpoints_to_test:
            success, response = self.make_request(method, endpoint, expected_status=200)
            
            if success:
                successful_requests += 1
                print(f"   ✅ {endpoint}: Token accepted")
            else:
                print(f"   ❌ {endpoint}: Token rejected")
        
        overall_success = successful_requests == len(endpoints_to_test)
        self.log_test("Session/Token Persistence", overall_success, 
                     f"- {successful_requests}/{len(endpoints_to_test)} requests successful with same token")
        return overall_success

    def test_authentication_timing(self):
        """Test authentication response times"""
        print("\n🔍 TESTING: Authentication Performance")
        
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        response_times = []
        successful_logins = 0
        
        # Test multiple login attempts to check consistency
        for i in range(3):
            start_time = time.time()
            success, response = self.make_request('POST', 'auth/login', login_data, 200)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if success:
                successful_logins += 1
                print(f"   ⏱️  Login {i+1}: {response_time:.3f}s")
            else:
                print(f"   ❌ Login {i+1}: Failed")
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Consider performance acceptable if average < 2s and max < 5s
            performance_acceptable = avg_response_time < 2.0 and max_response_time < 5.0
            
            print(f"   📊 Average Response Time: {avg_response_time:.3f}s")
            print(f"   📊 Max Response Time: {max_response_time:.3f}s")
        else:
            performance_acceptable = False
        
        overall_success = successful_logins == 3 and performance_acceptable
        self.log_test("Authentication Performance", overall_success, 
                     f"- Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
        return overall_success

    def test_backend_error_logs(self):
        """Check for backend errors that might affect authentication"""
        print("\n🔍 TESTING: Backend Error Detection")
        
        # Test various scenarios that might cause backend errors
        test_scenarios = [
            {
                "name": "Malformed JSON",
                "data": "invalid json",
                "headers": {'Content-Type': 'application/json'},
                "expected_status": 422
            },
            {
                "name": "Missing Content-Type",
                "data": {"email": "admin@test.com", "password": "admin123"},
                "headers": {},
                "expected_status": 200  # Should still work
            }
        ]
        
        successful_tests = 0
        
        for scenario in test_scenarios:
            url = f"{self.api_url}/auth/login"
            
            try:
                if scenario["name"] == "Malformed JSON":
                    response = requests.post(url, data=scenario["data"], 
                                           headers=scenario["headers"], timeout=10)
                else:
                    response = requests.post(url, json=scenario["data"], 
                                           headers=scenario["headers"], timeout=10)
                
                success = response.status_code == scenario["expected_status"]
                
                if success:
                    successful_tests += 1
                    print(f"   ✅ {scenario['name']}: Handled correctly ({response.status_code})")
                else:
                    print(f"   ❌ {scenario['name']}: Expected {scenario['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                print(f"   🔥 {scenario['name']}: Exception - {str(e)}")
        
        overall_success = successful_tests >= len(test_scenarios) - 1  # Allow one failure
        self.log_test("Backend Error Detection", overall_success, 
                     f"- {successful_tests}/{len(test_scenarios)} scenarios handled properly")
        return overall_success

    def run_comprehensive_auth_tests(self):
        """Run all authentication tests"""
        print("🚀 STARTING COMPREHENSIVE AUTHENTICATION SYSTEM TESTING")
        print("=" * 70)
        print("🎯 OBJECTIVE: Diagnose mobile login issues for admin@test.com / admin123")
        print("=" * 70)
        
        # Run all tests
        test_methods = [
            self.test_admin_user_exists,
            self.test_login_api_structure,
            self.test_token_validation,
            self.test_invalid_credentials,
            self.test_invalid_token_handling,
            self.test_cors_headers,
            self.test_mobile_user_agent_login,
            self.test_session_persistence,
            self.test_authentication_timing,
            self.test_backend_error_logs
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"🔥 Test {test_method.__name__} failed with exception: {str(e)}")
                self.log_test(test_method.__name__, False, f"- Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 AUTHENTICATION TESTING SUMMARY")
        print("=" * 70)
        print(f"🧪 Total Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
            print("✅ The authentication system appears to be working correctly.")
            print("🔍 Mobile login issues may be frontend-related or network-related.")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} AUTHENTICATION ISSUES FOUND!")
            print("❌ Backend authentication problems detected.")
            
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']} {result['details']}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = AuthenticationTester()
    success = tester.run_comprehensive_auth_tests()
    sys.exit(0 if success else 1)