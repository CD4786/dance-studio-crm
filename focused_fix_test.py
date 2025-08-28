import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class FocusedFixTester:
    def __init__(self, base_url="https://dance-admin-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_teacher_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if not success:
                print(f"   Status: {response.status_code}, Expected: {expected_status}")
                print(f"   Response: {response_data}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {str(e)}")
            return False, {"error": str(e)}

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("\n📋 AUTHENTICATION SETUP")
        
        # Register a test user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"test_owner_{timestamp}@example.com",
            "name": f"Test Owner {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        if not success:
            print("❌ Cannot proceed without user registration")
            return False
            
        self.user_id = response.get('id')
        
        # Login
        login_data = {
            "email": user_data['email'],
            "password": user_data['password']
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if not success:
            print("❌ Cannot proceed without user login")
            return False
            
        self.token = response.get('access_token')
        print(f"✅ Authentication setup complete - Token: {'Yes' if self.token else 'No'}")
        return True

    def setup_teacher(self):
        """Create a teacher for color testing"""
        print("\n📋 SETUP FOR COLOR TESTING")
        
        teacher_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1234567890",
            "specialties": ["ballet", "contemporary"],
            "bio": "Experienced ballet instructor with 10+ years of teaching."
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            print("❌ Cannot proceed without teachers for color testing")
            return False
            
        self.created_teacher_id = response.get('id')
        print(f"✅ Created teacher: {teacher_data['name']} (ID: {self.created_teacher_id})")
        return True

    def test_color_validation_fix(self):
        """Test the specific color validation fix mentioned in review request"""
        print("\n🎨 TESTING COLOR VALIDATION FIX")
        
        if not self.created_teacher_id:
            self.log_test("Color Validation Fix", False, "- No teacher ID available")
            return False
        
        # Test invalid hex codes that should be rejected
        invalid_hex_codes = ["#gggggg", "#12345", "#abcdefg", "invalid"]
        invalid_tests_passed = 0
        
        print("   Testing invalid hex codes (should be rejected):")
        for color in invalid_hex_codes:
            color_data = {"color": color}
            success, response = self.make_request('PUT', f'teachers/{self.created_teacher_id}/color', 
                                                color_data, 400)
            if success:
                invalid_tests_passed += 1
                print(f"   ✅ {color}: Correctly rejected with 400 error")
            else:
                print(f"   ❌ {color}: Should have been rejected but wasn't")
        
        # Test valid hex codes that should be accepted
        valid_hex_codes = ["#ff6b6b", "#3b82f6", "#ABCDEF"]
        valid_tests_passed = 0
        
        print("   Testing valid hex codes (should be accepted):")
        for color in valid_hex_codes:
            color_data = {"color": color}
            success, response = self.make_request('PUT', f'teachers/{self.created_teacher_id}/color', 
                                                color_data, 200)
            if success:
                returned_color = response.get('color')
                if returned_color == color:
                    valid_tests_passed += 1
                    print(f"   ✅ {color}: Accepted and returned correctly")
                else:
                    print(f"   ❌ {color}: Accepted but returned {returned_color}")
            else:
                print(f"   ❌ {color}: Should have been accepted but was rejected")
        
        # Test both uppercase and lowercase hex characters
        case_test_colors = ["#abcdef", "#ABCDEF", "#AbCdEf"]
        case_tests_passed = 0
        
        print("   Testing case sensitivity (all should work):")
        for color in case_test_colors:
            color_data = {"color": color}
            success, response = self.make_request('PUT', f'teachers/{self.created_teacher_id}/color', 
                                                color_data, 200)
            if success:
                case_tests_passed += 1
                print(f"   ✅ {color}: Case handled correctly")
            else:
                print(f"   ❌ {color}: Case sensitivity issue")
        
        total_tests = len(invalid_hex_codes) + len(valid_hex_codes) + len(case_test_colors)
        passed_tests = invalid_tests_passed + valid_tests_passed + case_tests_passed
        success = passed_tests == total_tests
        
        self.log_test("Color Validation Fix", success, 
                     f"- {passed_tests}/{total_tests} color validation tests passed")
        return success

    def test_user_listing_endpoint_fix(self):
        """Test the specific user listing endpoint fix mentioned in review request"""
        print("\n👥 TESTING USER LISTING ENDPOINT FIX")
        
        # Test with owner role (should work)
        print("   Testing with owner role:")
        if not self.token:
            self.log_test("User Listing Endpoint Fix", False, "- No owner token available")
            return False
            
        success, response = self.make_request('GET', 'users', expected_status=200)
        owner_test_passed = success
        
        if success:
            users_count = len(response) if isinstance(response, list) else 0
            print(f"   ✅ Owner role: Successfully retrieved {users_count} users")
        else:
            print(f"   ❌ Owner role: Failed to retrieve users - got error instead of user list")
        
        # Create and test with manager role (should work)
        print("   Testing with manager role:")
        manager_data = {
            "email": f"manager_fix_test_{datetime.now().strftime('%H%M%S')}@example.com",
            "name": "Manager Fix Test",
            "password": "ManagerPass123!",
            "role": "manager"
        }
        
        success, manager_response = self.make_request('POST', 'users', manager_data, 200)
        if not success:
            print("   ❌ Manager role: Failed to create manager user for testing")
            manager_test_passed = False
        else:
            # Login as manager
            login_data = {
                "email": manager_data["email"],
                "password": manager_data["password"]
            }
            
            success, login_response = self.make_request('POST', 'auth/login', login_data, 200)
            if not success:
                print("   ❌ Manager role: Failed to login as manager")
                manager_test_passed = False
            else:
                # Save original token and use manager token
                original_token = self.token
                self.token = login_response.get('access_token')
                
                # Test user listing with manager permissions
                success, response = self.make_request('GET', 'users', expected_status=200)
                manager_test_passed = success
                
                if success:
                    users_count = len(response) if isinstance(response, list) else 0
                    print(f"   ✅ Manager role: Successfully retrieved {users_count} users")
                else:
                    print(f"   ❌ Manager role: Failed to retrieve users - got error instead of user list")
                
                # Restore original token
                self.token = original_token
        
        # Create and test with teacher role (should get 403)
        print("   Testing with teacher role (should get 403):")
        teacher_data = {
            "email": f"teacher_fix_test_{datetime.now().strftime('%H%M%S')}@example.com",
            "name": "Teacher Fix Test",
            "password": "TeacherPass123!",
            "role": "teacher"
        }
        
        success, teacher_response = self.make_request('POST', 'users', teacher_data, 200)
        if not success:
            print("   ❌ Teacher role: Failed to create teacher user for testing")
            teacher_test_passed = False
        else:
            # Login as teacher
            login_data = {
                "email": teacher_data["email"],
                "password": teacher_data["password"]
            }
            
            success, login_response = self.make_request('POST', 'auth/login', login_data, 200)
            if not success:
                print("   ❌ Teacher role: Failed to login as teacher")
                teacher_test_passed = False
            else:
                # Save original token and use teacher token
                original_token = self.token
                self.token = login_response.get('access_token')
                
                # Test user listing with teacher permissions (should get 403)
                success, response = self.make_request('GET', 'users', expected_status=403)
                teacher_test_passed = success
                
                if success:
                    print(f"   ✅ Teacher role: Correctly denied access with 403")
                else:
                    print(f"   ❌ Teacher role: Should have been denied access but wasn't")
                
                # Restore original token
                self.token = original_token
        
        # Check response format and data integrity for owner
        print("   Testing response format and data integrity:")
        success, response = self.make_request('GET', 'users', expected_status=200)
        format_test_passed = False
        
        if success and isinstance(response, list) and len(response) > 0:
            first_user = response[0]
            required_fields = ['id', 'email', 'name', 'role', 'is_active', 'created_at']
            has_required_fields = all(field in first_user for field in required_fields)
            
            if has_required_fields:
                format_test_passed = True
                print(f"   ✅ Response format: All required fields present")
            else:
                missing_fields = [field for field in required_fields if field not in first_user]
                print(f"   ❌ Response format: Missing fields: {missing_fields}")
        else:
            print(f"   ❌ Response format: Invalid response structure")
        
        # Overall success
        all_tests_passed = owner_test_passed and manager_test_passed and teacher_test_passed and format_test_passed
        
        self.log_test("User Listing Endpoint Fix", all_tests_passed, 
                     f"- Owner: {'✅' if owner_test_passed else '❌'}, Manager: {'✅' if manager_test_passed else '❌'}, Teacher: {'✅' if teacher_test_passed else '❌'}, Format: {'✅' if format_test_passed else '❌'}")
        return all_tests_passed

    def test_overall_system_health_check(self):
        """Test overall system health after the fixes"""
        print("\n🏥 OVERALL SYSTEM HEALTH CHECK")
        
        health_tests = []
        
        # Test major endpoints are still working
        print("   Testing major endpoints:")
        
        # Dashboard
        success, response = self.make_request('GET', 'dashboard/stats', expected_status=200)
        health_tests.append(("Dashboard Stats", success))
        if success:
            print("   ✅ Dashboard stats endpoint working")
        else:
            print("   ❌ Dashboard stats endpoint failed")
        
        # Teachers
        success, response = self.make_request('GET', 'teachers', expected_status=200)
        health_tests.append(("Teachers List", success))
        if success:
            print("   ✅ Teachers list endpoint working")
        else:
            print("   ❌ Teachers list endpoint failed")
        
        # Students
        success, response = self.make_request('GET', 'students', expected_status=200)
        health_tests.append(("Students List", success))
        if success:
            print("   ✅ Students list endpoint working")
        else:
            print("   ❌ Students list endpoint failed")
        
        # Settings system
        success, response = self.make_request('GET', 'settings', expected_status=200)
        health_tests.append(("Settings System", success))
        if success:
            print("   ✅ Settings system working")
        else:
            print("   ❌ Settings system failed")
        
        # Teacher color management
        if self.created_teacher_id:
            success, response = self.make_request('GET', f'teachers/{self.created_teacher_id}/color', expected_status=200)
            health_tests.append(("Teacher Color Management", success))
            if success:
                print("   ✅ Teacher color management working")
            else:
                print("   ❌ Teacher color management failed")
        
        # User management CRUD
        success, response = self.make_request('GET', 'users', expected_status=200)
        health_tests.append(("User Management", success))
        if success:
            print("   ✅ User management working")
        else:
            print("   ❌ User management failed")
        
        # Calculate overall health
        passed_tests = sum(1 for _, success in health_tests if success)
        total_tests = len(health_tests)
        overall_health = passed_tests == total_tests
        
        self.log_test("Overall System Health Check", overall_health, 
                     f"- {passed_tests}/{total_tests} major endpoints working")
        return overall_health

    def run_focused_fix_tests(self):
        """Run focused tests for the two specific fixes mentioned in review request"""
        print("🎯 FOCUSED TESTING FOR SPECIFIC FIXES")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            return
        
        if not self.setup_teacher():
            return
        
        # Run the specific fix tests
        print("\n📋 SPECIFIC FIX TESTS")
        color_fix_success = self.test_color_validation_fix()
        user_listing_fix_success = self.test_user_listing_endpoint_fix()
        health_check_success = self.test_overall_system_health_check()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"🏁 FOCUSED FIX TEST SUMMARY")
        print(f"   Color Validation Fix: {'✅ PASSED' if color_fix_success else '❌ FAILED'}")
        print(f"   User Listing Fix: {'✅ PASSED' if user_listing_fix_success else '❌ FAILED'}")
        print(f"   System Health Check: {'✅ PASSED' if health_check_success else '❌ FAILED'}")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if color_fix_success and user_listing_fix_success and health_check_success:
            print("🎉 ALL FOCUSED TESTS PASSED - FIXES VERIFIED!")
        else:
            failed_tests = []
            if not color_fix_success:
                failed_tests.append("Color Validation Fix")
            if not user_listing_fix_success:
                failed_tests.append("User Listing Fix")
            if not health_check_success:
                failed_tests.append("System Health Check")
            print(f"⚠️  Failed tests: {', '.join(failed_tests)}")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = FocusedFixTester()
    tester.run_focused_fix_tests()