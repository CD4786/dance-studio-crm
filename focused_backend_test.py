#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class FocusedBackendTester:
    def __init__(self, base_url="https://rhythm-scheduler-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0

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
        # Try to register a new user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"test_owner_{timestamp}@example.com",
            "name": f"Test Owner {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success:
            self.user_id = response.get('id')
            self.test_email = user_data['email']
            self.test_password = user_data['password']
            
            # Now login
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            success, response = self.make_request('POST', 'auth/login', login_data, 200)
            
            if success:
                self.token = response.get('access_token')
                
        self.log_test("Authentication Setup", success and self.token is not None, 
                     f"- Token received: {'Yes' if self.token else 'No'}")
        return success and self.token is not None

    def test_dashboard_stats_health_check(self):
        """Test GET /api/dashboard/stats endpoint to verify backend is responsive and database connectivity"""
        success, response = self.make_request('GET', 'dashboard/stats', expected_status=200)
        
        if success:
            required_fields = ['total_classes', 'total_teachers', 'total_students', 'active_enrollments', 
                             'classes_today', 'lessons_today', 'lessons_attended_today', 'estimated_monthly_revenue']
            has_all_fields = all(field in response for field in required_fields)
            
            if has_all_fields:
                # Check that we have reasonable data
                total_teachers = response.get('total_teachers', 0)
                total_students = response.get('total_students', 0)
                active_enrollments = response.get('active_enrollments', 0)
                
                print(f"   📊 Dashboard Stats:")
                print(f"      - Total Teachers: {total_teachers}")
                print(f"      - Total Students: {total_students}")
                print(f"      - Active Enrollments: {active_enrollments}")
                print(f"      - Lessons Today: {response.get('lessons_today', 0)}")
                print(f"      - Estimated Monthly Revenue: ${response.get('estimated_monthly_revenue', 0)}")
                
                success = has_all_fields
            else:
                missing_fields = [field for field in required_fields if field not in response]
                print(f"   ❌ Missing fields: {missing_fields}")
                success = False
            
        self.log_test("Dashboard Stats Health Check", success, 
                     f"- Database connectivity and API responsiveness verified")
        return success

    def test_student_management_api(self):
        """Test GET /api/students to ensure student data is returned properly for search/filtering functionality"""
        success, response = self.make_request('GET', 'students', expected_status=200)
        
        if success:
            students_count = len(response) if isinstance(response, list) else 0
            
            if students_count > 0:
                # Check that students have all required fields for search/filtering
                sample_student = response[0]
                required_fields = ['name', 'email', 'phone', 'parent_name', 'parent_email', 'notes', 'created_at']
                
                available_fields = []
                for field in required_fields:
                    if field in sample_student:
                        available_fields.append(field)
                
                print(f"   👥 Student Data Analysis:")
                print(f"      - Total Students: {students_count}")
                print(f"      - Available Fields: {available_fields}")
                print(f"      - Sample Student: {sample_student.get('name', 'Unknown')}")
                
                # Verify essential fields for search functionality
                essential_fields = ['name', 'email', 'created_at']
                has_essential_fields = all(field in sample_student for field in essential_fields)
                
                success = has_essential_fields
            else:
                print(f"   ℹ️  No students found in database")
                success = True  # Empty result is still a successful API call
            
        self.log_test("Student Management API", success, 
                     f"- Found {students_count} students with proper field structure")
        return success

    def test_lesson_management_api(self):
        """Test GET /api/lessons endpoint for instructor stats calculation"""
        success, response = self.make_request('GET', 'lessons', expected_status=200)
        
        if success:
            lessons_count = len(response) if isinstance(response, list) else 0
            
            if lessons_count > 0:
                # Check that lessons have teacher_ids arrays for instructor stats
                sample_lesson = response[0]
                
                # Check for new teacher_ids array format
                has_teacher_ids = 'teacher_ids' in sample_lesson
                has_teacher_names = 'teacher_names' in sample_lesson
                has_booking_type = 'booking_type' in sample_lesson
                has_datetime = 'start_datetime' in sample_lesson
                
                print(f"   📚 Lesson Data Analysis:")
                print(f"      - Total Lessons: {lessons_count}")
                print(f"      - Has teacher_ids array: {has_teacher_ids}")
                print(f"      - Has teacher_names array: {has_teacher_names}")
                print(f"      - Has booking_type: {has_booking_type}")
                print(f"      - Has datetime info: {has_datetime}")
                
                if has_teacher_ids:
                    teacher_ids = sample_lesson.get('teacher_ids', [])
                    teacher_names = sample_lesson.get('teacher_names', [])
                    print(f"      - Sample lesson teachers: {len(teacher_ids)} ({teacher_names})")
                
                # Verify essential fields for instructor stats calculation
                success = has_teacher_ids and has_datetime
            else:
                print(f"   ℹ️  No lessons found in database")
                success = True  # Empty result is still a successful API call
            
        self.log_test("Lesson Management API", success, 
                     f"- Found {lessons_count} lessons with proper teacher_ids arrays")
        return success

    def test_authentication_system(self):
        """Quick verification that auth endpoints are working"""
        # Test token validation by accessing a protected endpoint
        if not self.token:
            self.log_test("Authentication System", False, "- No token available for testing")
            return False
            
        # Test accessing a protected endpoint
        success, response = self.make_request('GET', 'students', expected_status=200)
        
        if success:
            print(f"   🔐 Authentication Status:")
            print(f"      - Token validation: Working")
            print(f"      - Protected endpoint access: Successful")
            print(f"      - User role: Owner (full access)")
        
        self.log_test("Authentication System", success, 
                     f"- JWT token validation and protected endpoint access working")
        return success

    def test_settings_system(self):
        """Verify GET /api/settings endpoints are working"""
        # Test getting all settings
        success, response = self.make_request('GET', 'settings', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            # Check for different categories
            categories = set()
            for setting in response:
                categories.add(setting.get('category', ''))
            
            print(f"   ⚙️  Settings System Analysis:")
            print(f"      - Total Settings: {settings_count}")
            print(f"      - Categories: {sorted(list(categories))}")
            
            # Test getting theme settings specifically (mentioned in previous testing)
            theme_success, theme_response = self.make_request('GET', 'settings/theme', expected_status=200)
            
            if theme_success:
                theme_settings_count = len(theme_response) if isinstance(theme_response, list) else 0
                print(f"      - Theme Settings: {theme_settings_count}")
                
                # Check for specific theme setting
                selected_theme_success, selected_theme_response = self.make_request('GET', 'settings/theme/selected_theme', expected_status=200)
                
                if selected_theme_success:
                    theme_value = selected_theme_response.get('value', 'Unknown')
                    print(f"      - Current Theme: {theme_value}")
            
            success = success and theme_success and selected_theme_success
            
        self.log_test("Settings System", success, 
                     f"- Settings endpoints working with {settings_count} total settings")
        return success

    def test_comprehensive_api_functionality(self):
        """Run comprehensive test of all endpoints mentioned in review request"""
        print("🎯 FOCUSED BACKEND API TESTING")
        print("=" * 80)
        print("Testing endpoints related to frontend fixes:")
        print("1. Dashboard Stats (health check)")
        print("2. Student Management (search/filtering support)")
        print("3. Lesson Management (instructor stats calculation)")
        print("4. Authentication System (auth-protected components)")
        print("5. Settings System (theme and configuration)")
        print("=" * 80)
        
        # Setup authentication first
        if not self.setup_authentication():
            print("❌ Failed to setup authentication - cannot continue with protected endpoint tests")
            return False
        
        # Run all focused tests
        tests = [
            self.test_dashboard_stats_health_check,
            self.test_student_management_api,
            self.test_lesson_management_api,
            self.test_authentication_system,
            self.test_settings_system
        ]
        
        for test in tests:
            test()
            print()  # Add spacing between tests
        
        # Print summary
        print("=" * 80)
        print(f"📊 FOCUSED BACKEND TEST RESULTS")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        print("=" * 80)
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL FOCUSED BACKEND TESTS PASSED!")
            return True
        else:
            print("⚠️  Some tests failed - see details above")
            return False

def main():
    tester = FocusedBackendTester()
    success = tester.test_comprehensive_api_functionality()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()