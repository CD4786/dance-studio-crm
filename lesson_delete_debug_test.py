#!/usr/bin/env python3
"""
Focused test script to debug lesson deletion issues reported by user.
This script specifically tests the DELETE /api/lessons/{lesson_id} endpoint
to identify why users are getting "failed to delete lesson" errors.
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

class LessonDeleteDebugger:
    def __init__(self, base_url="https://dance-studio-crm.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.test_student_id = None
        self.test_teacher_id = None
        self.test_lesson_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results with detailed output"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return detailed response information"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Making {method} request to: {url}")
        if data:
            print(f"📤 Request data: {json.dumps(data, indent=2)}")
        print(f"🔑 Headers: {json.dumps(headers, indent=2)}")

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
                print(f"📥 Response JSON: {json.dumps(response_data, indent=2)}")
            except:
                response_data = {"raw_response": response.text}
                print(f"📥 Response Text: {response.text}")

            if not success:
                print(f"⚠️  Expected Status: {expected_status}, Got: {response.status_code}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            return False, {"error": str(e)}

    def setup_authentication(self):
        """Set up authentication for testing"""
        print("\n🔐 Setting up authentication...")
        
        # Register a test user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"lesson_delete_test_{timestamp}@example.com",
            "name": f"Lesson Delete Tester {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Debug Test Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if not success:
            self.log_test("User Registration", False, f"- Failed to register user")
            return False
            
        self.user_id = response.get('id')
        self.test_email = user_data['email']
        self.test_password = user_data['password']
        
        # Login to get token
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            
        self.log_test("Authentication Setup", success, f"- Token: {'✓' if self.token else '✗'}")
        return success

    def create_test_data(self):
        """Create test student, teacher, and lesson for deletion testing"""
        print("\n📝 Creating test data...")
        
        # Create test student
        student_data = {
            "name": "Test Student for Deletion",
            "email": "test.student.delete@example.com",
            "phone": "+1555000001",
            "notes": "Student created for lesson deletion testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Create Test Student", False, "- Failed to create student")
            return False
            
        self.test_student_id = response.get('id')
        self.log_test("Create Test Student", True, f"- Student ID: {self.test_student_id}")
        
        # Create test teacher
        teacher_data = {
            "name": "Test Teacher for Deletion",
            "email": "test.teacher.delete@example.com",
            "phone": "+1555000002",
            "specialties": ["ballet", "jazz"],
            "bio": "Teacher created for lesson deletion testing"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Create Test Teacher", False, "- Failed to create teacher")
            return False
            
        self.test_teacher_id = response.get('id')
        self.log_test("Create Test Teacher", True, f"- Teacher ID: {self.test_teacher_id}")
        
        # Create test lesson
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.test_student_id,
            "teacher_id": self.test_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Test lesson for deletion debugging"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Create Test Lesson", False, "- Failed to create lesson")
            return False
            
        self.test_lesson_id = response.get('id')
        self.log_test("Create Test Lesson", True, f"- Lesson ID: {self.test_lesson_id}")
        
        return True

    def test_delete_lesson_with_valid_auth(self):
        """Test DELETE lesson with valid authentication"""
        print("\n🔍 Testing DELETE lesson with valid authentication...")
        
        if not self.test_lesson_id:
            self.log_test("Delete Lesson with Valid Auth", False, "- No test lesson available")
            return False
            
        success, response = self.make_request('DELETE', f'lessons/{self.test_lesson_id}', expected_status=200)
        
        if success:
            message = response.get('message', 'No message')
            print(f"✅ Delete successful: {message}")
        else:
            print(f"❌ Delete failed: {response}")
            
        self.log_test("Delete Lesson with Valid Auth", success, f"- Response: {response}")
        return success

    def test_delete_lesson_without_auth(self):
        """Test DELETE lesson without authentication"""
        print("\n🔍 Testing DELETE lesson without authentication...")
        
        # Create another lesson for this test
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.test_student_id,
            "teacher_id": self.test_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Test lesson for auth testing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Delete Lesson without Auth", False, "- Failed to create test lesson")
            return False
            
        test_lesson_id = response.get('id')
        
        # Remove token temporarily
        original_token = self.token
        self.token = None
        
        success, response = self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=403)
        
        # Restore token
        self.token = original_token
        
        self.log_test("Delete Lesson without Auth", success, f"- Expected 403, got response: {response}")
        
        # Clean up the test lesson
        self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=200)
        
        return success

    def test_delete_lesson_with_invalid_auth(self):
        """Test DELETE lesson with invalid authentication token"""
        print("\n🔍 Testing DELETE lesson with invalid authentication...")
        
        # Create another lesson for this test
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.test_student_id,
            "teacher_id": self.test_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Test lesson for invalid auth testing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Delete Lesson with Invalid Auth", False, "- Failed to create test lesson")
            return False
            
        test_lesson_id = response.get('id')
        
        # Use invalid token
        original_token = self.token
        self.token = "invalid.jwt.token"
        
        success, response = self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=401)
        
        # Restore token
        self.token = original_token
        
        self.log_test("Delete Lesson with Invalid Auth", success, f"- Expected 401, got response: {response}")
        
        # Clean up the test lesson
        self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=200)
        
        return success

    def test_delete_nonexistent_lesson(self):
        """Test DELETE lesson with non-existent lesson ID"""
        print("\n🔍 Testing DELETE lesson with non-existent ID...")
        
        fake_lesson_id = "nonexistent-lesson-id-12345"
        
        success, response = self.make_request('DELETE', f'lessons/{fake_lesson_id}', expected_status=404)
        
        self.log_test("Delete Non-existent Lesson", success, f"- Expected 404, got response: {response}")
        return success

    def test_lesson_exists_before_delete(self):
        """Test that lesson exists before attempting deletion"""
        print("\n🔍 Testing lesson existence before deletion...")
        
        # Create a lesson specifically for this test
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=13, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.test_student_id,
            "teacher_id": self.test_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Test lesson for existence verification"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Lesson Exists Before Delete", False, "- Failed to create test lesson")
            return False
            
        test_lesson_id = response.get('id')
        
        # Verify lesson exists by getting it
        success, response = self.make_request('GET', f'lessons/{test_lesson_id}', expected_status=200)
        
        if success:
            lesson_name = f"{response.get('student_name', 'Unknown')} with {response.get('teacher_name', 'Unknown')}"
            print(f"✅ Lesson exists: {lesson_name}")
            
            # Now delete it
            delete_success, delete_response = self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=200)
            
            if delete_success:
                # Verify lesson is gone
                verify_success, verify_response = self.make_request('GET', f'lessons/{test_lesson_id}', expected_status=404)
                success = delete_success and verify_success
            else:
                success = False
        
        self.log_test("Lesson Exists Before Delete", success, f"- Lesson verified and deleted successfully")
        return success

    def test_lesson_id_format_validation(self):
        """Test DELETE with various lesson ID formats"""
        print("\n🔍 Testing lesson ID format validation...")
        
        test_cases = [
            ("", "Empty ID"),
            ("   ", "Whitespace ID"),
            ("invalid-uuid-format", "Invalid UUID format"),
            ("12345", "Numeric ID"),
            ("null", "Null string"),
            ("undefined", "Undefined string")
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for test_id, description in test_cases:
            print(f"\n  Testing {description}: '{test_id}'")
            
            # Most should return 404 (not found) rather than 400 (bad request)
            # because the server treats them as valid strings that just don't exist
            success, response = self.make_request('DELETE', f'lessons/{test_id}', expected_status=404)
            
            if success:
                passed_tests += 1
                print(f"  ✅ {description} handled correctly (404)")
            else:
                print(f"  ❌ {description} not handled correctly: {response}")
        
        overall_success = passed_tests == total_tests
        self.log_test("Lesson ID Format Validation", overall_success, 
                     f"- {passed_tests}/{total_tests} ID formats handled correctly")
        return overall_success

    def test_concurrent_lesson_deletion(self):
        """Test what happens when trying to delete the same lesson multiple times"""
        print("\n🔍 Testing concurrent/repeated lesson deletion...")
        
        # Create a lesson for this test
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.test_student_id,
            "teacher_id": self.test_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Test lesson for concurrent deletion"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Concurrent Lesson Deletion", False, "- Failed to create test lesson")
            return False
            
        test_lesson_id = response.get('id')
        
        # First deletion should succeed
        success1, response1 = self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=200)
        
        # Second deletion should return 404 (not found)
        success2, response2 = self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=404)
        
        overall_success = success1 and success2
        
        self.log_test("Concurrent Lesson Deletion", overall_success, 
                     f"- First delete: {'✓' if success1 else '✗'}, Second delete: {'✓' if success2 else '✗'}")
        return overall_success

    def test_delete_lesson_with_enrollment_link(self):
        """Test deleting a lesson that's linked to an enrollment"""
        print("\n🔍 Testing deletion of lesson linked to enrollment...")
        
        # Create an enrollment first
        enrollment_data = {
            "student_id": self.test_student_id,
            "program_name": "Test Program for Deletion",
            "total_lessons": 5,
            "total_paid": 250.0
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if not success:
            self.log_test("Delete Lesson with Enrollment Link", False, "- Failed to create enrollment")
            return False
            
        enrollment_id = response.get('id')
        
        # Create a lesson linked to this enrollment
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.test_student_id,
            "teacher_id": self.test_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Test lesson linked to enrollment",
            "enrollment_id": enrollment_id
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Delete Lesson with Enrollment Link", False, "- Failed to create linked lesson")
            return False
            
        test_lesson_id = response.get('id')
        
        # Delete the lesson
        success, response = self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=200)
        
        self.log_test("Delete Lesson with Enrollment Link", success, 
                     f"- Linked lesson deletion: {'✓' if success else '✗'}")
        
        # Clean up enrollment
        self.make_request('DELETE', f'enrollments/{enrollment_id}', expected_status=200)
        
        return success

    def run_comprehensive_debug(self):
        """Run all debug tests to identify lesson deletion issues"""
        print("🚀 Starting comprehensive lesson deletion debugging...")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot continue.")
            return False
            
        if not self.create_test_data():
            print("❌ Test data creation failed. Cannot continue.")
            return False
        
        # Run all debug tests
        test_methods = [
            self.test_delete_lesson_with_valid_auth,
            self.test_delete_lesson_without_auth,
            self.test_delete_lesson_with_invalid_auth,
            self.test_delete_nonexistent_lesson,
            self.test_lesson_exists_before_delete,
            self.test_lesson_id_format_validation,
            self.test_concurrent_lesson_deletion,
            self.test_delete_lesson_with_enrollment_link
        ]
        
        print(f"\n📋 Running {len(test_methods)} debug tests...")
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} crashed: {str(e)}")
                self.tests_run += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 LESSON DELETION DEBUG SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("\n✅ ALL TESTS PASSED - Lesson deletion functionality appears to be working correctly")
            print("🔍 The user's issue may be related to:")
            print("   - Frontend implementation problems")
            print("   - Network connectivity issues")
            print("   - Specific lesson IDs or data causing issues")
            print("   - Browser-specific problems")
        else:
            print(f"\n❌ {self.tests_run - self.tests_passed} TESTS FAILED - Issues found with lesson deletion")
            print("🔍 Review the failed tests above to identify the root cause")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    debugger = LessonDeleteDebugger()
    success = debugger.run_comprehensive_debug()
    sys.exit(0 if success else 1)