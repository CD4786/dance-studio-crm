import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class DeleteAuthenticationTester:
    def __init__(self, base_url="https://289f28fc-e8d9-451e-a1ca-a56433f8acd9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_teacher_id = None
        self.created_student_id = None
        self.created_lesson_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, expected_status: int = 200, use_auth: bool = True) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token and use_auth:
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
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            if not success:
                print(f"   Status: {response.status_code}, Expected: {expected_status}")
                print(f"   Response: {response_data}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {str(e)}")
            return False, {"error": str(e)}

    def test_user_registration_and_login(self):
        """Test user registration and login for authentication"""
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"delete_test_owner_{timestamp}@example.com",
            "name": f"Delete Test Owner {timestamp}",
            "password": "DeleteTestPassword123!",
            "role": "owner",
            "studio_name": "Delete Test Dance Studio"
        }
        
        # Register user
        success, response = self.make_request('POST', 'auth/register', user_data, 200, use_auth=False)
        
        if success:
            self.user_id = response.get('id')
            self.test_email = user_data['email']
            self.test_password = user_data['password']
            
        self.log_test("User Registration", success, f"- User ID: {self.user_id}")
        
        if not success:
            return False
            
        # Login user
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200, use_auth=False)
        
        if success:
            self.token = response.get('access_token')
            
        self.log_test("User Login", success, f"- Token received: {'Yes' if self.token else 'No'}")
        return success

    def setup_test_data(self):
        """Create test teacher, student, and lesson for delete testing"""
        # Create teacher
        teacher_data = {
            "name": "Delete Test Teacher",
            "email": "delete.teacher@example.com",
            "phone": "+1555123456",
            "specialties": ["ballet", "jazz"],
            "bio": "Teacher for delete testing"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if success:
            self.created_teacher_id = response.get('id')
            
        self.log_test("Setup Test Teacher", success, f"- Teacher ID: {self.created_teacher_id}")
        
        if not success:
            return False
            
        # Create student
        student_data = {
            "name": "Delete Test Student",
            "email": "delete.student@example.com",
            "phone": "+1555654321",
            "parent_name": "Delete Test Parent",
            "parent_phone": "+1555654322",
            "parent_email": "delete.parent@example.com",
            "notes": "Student for delete testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if success:
            self.created_student_id = response.get('id')
            
        self.log_test("Setup Test Student", success, f"- Student ID: {self.created_student_id}")
        
        if not success:
            return False
            
        # Create lesson
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Lesson for delete testing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if success:
            self.created_lesson_id = response.get('id')
            
        self.log_test("Setup Test Lesson", success, f"- Lesson ID: {self.created_lesson_id}")
        return success

    def test_delete_teacher_with_valid_auth(self):
        """Test deleting teacher with valid authentication"""
        if not self.created_teacher_id:
            self.log_test("Delete Teacher with Valid Auth", False, "- No teacher ID available")
            return False
            
        success, response = self.make_request('DELETE', f'teachers/{self.created_teacher_id}', expected_status=200)
        
        if success:
            message = response.get('message', '')
            associated_lessons = response.get('associated_lessons', 0)
            associated_classes = response.get('associated_classes', 0)
            
        self.log_test("Delete Teacher with Valid Auth", success, 
                     f"- Message: {message}, Lessons: {associated_lessons}, Classes: {associated_classes}")
        return success

    def test_delete_teacher_without_auth(self):
        """Test deleting teacher without authentication (should fail)"""
        # Create another teacher for this test
        teacher_data = {
            "name": "No Auth Delete Test Teacher",
            "email": "noauth.teacher@example.com",
            "phone": "+1555999888",
            "specialties": ["contemporary"],
            "bio": "Teacher for no-auth delete testing"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Delete Teacher without Auth", False, "- Failed to create test teacher")
            return False
            
        teacher_id = response.get('id')
        
        # Try to delete without authentication (should fail with 403 or 401)
        success, response = self.make_request('DELETE', f'teachers/{teacher_id}', expected_status=403, use_auth=False)
        
        # If 403 didn't work, try 401
        if not success:
            success, response = self.make_request('DELETE', f'teachers/{teacher_id}', expected_status=401, use_auth=False)
            
        self.log_test("Delete Teacher without Auth", success, f"- Expected auth error, got status: {response.get('status_code', 'unknown')}")
        
        # Clean up - delete with auth
        if teacher_id:
            self.make_request('DELETE', f'teachers/{teacher_id}', expected_status=200)
            
        return success

    def test_delete_teacher_with_invalid_auth(self):
        """Test deleting teacher with invalid authentication token"""
        # Create another teacher for this test
        teacher_data = {
            "name": "Invalid Auth Delete Test Teacher",
            "email": "invalidauth.teacher@example.com",
            "phone": "+1555777666",
            "specialties": ["tap"],
            "bio": "Teacher for invalid-auth delete testing"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Delete Teacher with Invalid Auth", False, "- Failed to create test teacher")
            return False
            
        teacher_id = response.get('id')
        
        # Save original token and use invalid token
        original_token = self.token
        self.token = "invalid_token_12345"
        
        # Try to delete with invalid token (should fail with 401)
        success, response = self.make_request('DELETE', f'teachers/{teacher_id}', expected_status=401)
        
        self.log_test("Delete Teacher with Invalid Auth", success, f"- Expected 401 error, got status: {response.get('status_code', 'unknown')}")
        
        # Restore original token and clean up
        self.token = original_token
        if teacher_id:
            self.make_request('DELETE', f'teachers/{teacher_id}', expected_status=200)
            
        return success

    def test_delete_student_with_valid_auth(self):
        """Test deleting student with valid authentication"""
        if not self.created_student_id:
            self.log_test("Delete Student with Valid Auth", False, "- No student ID available")
            return False
            
        success, response = self.make_request('DELETE', f'students/{self.created_student_id}', expected_status=200)
        
        if success:
            message = response.get('message', '')
            associated_lessons = response.get('associated_lessons', 0)
            associated_enrollments = response.get('associated_enrollments', 0)
            
        self.log_test("Delete Student with Valid Auth", success, 
                     f"- Message: {message}, Lessons: {associated_lessons}, Enrollments: {associated_enrollments}")
        return success

    def test_delete_student_without_auth(self):
        """Test deleting student without authentication (should fail)"""
        # Create another student for this test
        student_data = {
            "name": "No Auth Delete Test Student",
            "email": "noauth.student@example.com",
            "phone": "+1555888777",
            "notes": "Student for no-auth delete testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Delete Student without Auth", False, "- Failed to create test student")
            return False
            
        student_id = response.get('id')
        
        # Try to delete without authentication (should fail with 403 or 401)
        success, response = self.make_request('DELETE', f'students/{student_id}', expected_status=403, use_auth=False)
        
        # If 403 didn't work, try 401
        if not success:
            success, response = self.make_request('DELETE', f'students/{student_id}', expected_status=401, use_auth=False)
            
        self.log_test("Delete Student without Auth", success, f"- Expected auth error, got status: {response.get('status_code', 'unknown')}")
        
        # Clean up - delete with auth
        if student_id:
            self.make_request('DELETE', f'students/{student_id}', expected_status=200)
            
        return success

    def test_delete_student_with_invalid_auth(self):
        """Test deleting student with invalid authentication token"""
        # Create another student for this test
        student_data = {
            "name": "Invalid Auth Delete Test Student",
            "email": "invalidauth.student@example.com",
            "phone": "+1555666555",
            "notes": "Student for invalid-auth delete testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Delete Student with Invalid Auth", False, "- Failed to create test student")
            return False
            
        student_id = response.get('id')
        
        # Save original token and use invalid token
        original_token = self.token
        self.token = "invalid_token_67890"
        
        # Try to delete with invalid token (should fail with 401)
        success, response = self.make_request('DELETE', f'students/{student_id}', expected_status=401)
        
        self.log_test("Delete Student with Invalid Auth", success, f"- Expected 401 error, got status: {response.get('status_code', 'unknown')}")
        
        # Restore original token and clean up
        self.token = original_token
        if student_id:
            self.make_request('DELETE', f'students/{student_id}', expected_status=200)
            
        return success

    def test_delete_lesson_with_valid_auth(self):
        """Test deleting lesson with valid authentication"""
        if not self.created_lesson_id:
            self.log_test("Delete Lesson with Valid Auth", False, "- No lesson ID available")
            return False
            
        success, response = self.make_request('DELETE', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        if success:
            message = response.get('message', '')
            
        self.log_test("Delete Lesson with Valid Auth", success, f"- Message: {message}")
        return success

    def test_delete_lesson_without_auth(self):
        """Test deleting lesson without authentication (should fail)"""
        # Create another lesson for this test
        if not self.created_teacher_id or not self.created_student_id:
            self.log_test("Delete Lesson without Auth", False, "- No teacher or student ID available")
            return False
            
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Lesson for no-auth delete testing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Delete Lesson without Auth", False, "- Failed to create test lesson")
            return False
            
        lesson_id = response.get('id')
        
        # Try to delete without authentication (should fail with 403 or 401)
        success, response = self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=403, use_auth=False)
        
        # If 403 didn't work, try 401
        if not success:
            success, response = self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=401, use_auth=False)
            
        self.log_test("Delete Lesson without Auth", success, f"- Expected auth error, got status: {response.get('status_code', 'unknown')}")
        
        # Clean up - delete with auth
        if lesson_id:
            self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=200)
            
        return success

    def test_delete_lesson_with_invalid_auth(self):
        """Test deleting lesson with invalid authentication token"""
        # Create another lesson for this test
        if not self.created_teacher_id or not self.created_student_id:
            self.log_test("Delete Lesson with Invalid Auth", False, "- No teacher or student ID available")
            return False
            
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=16, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Lesson for invalid-auth delete testing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Delete Lesson with Invalid Auth", False, "- Failed to create test lesson")
            return False
            
        lesson_id = response.get('id')
        
        # Save original token and use invalid token
        original_token = self.token
        self.token = "invalid_token_lesson_123"
        
        # Try to delete with invalid token (should fail with 401)
        success, response = self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=401)
        
        self.log_test("Delete Lesson with Invalid Auth", success, f"- Expected 401 error, got status: {response.get('status_code', 'unknown')}")
        
        # Restore original token and clean up
        self.token = original_token
        if lesson_id:
            self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=200)
            
        return success

    def test_delete_nonexistent_records(self):
        """Test deleting non-existent records with valid auth"""
        fake_ids = ["nonexistent-teacher-id", "nonexistent-student-id", "nonexistent-lesson-id"]
        
        # Test teacher
        success, response = self.make_request('DELETE', f'teachers/{fake_ids[0]}', expected_status=404)
        self.log_test("Delete Nonexistent Teacher", success, "- Expected 404 error")
        
        # Test student  
        success, response = self.make_request('DELETE', f'students/{fake_ids[1]}', expected_status=404)
        self.log_test("Delete Nonexistent Student", success, "- Expected 404 error")
        
        # Test lesson
        success, response = self.make_request('DELETE', f'lessons/{fake_ids[2]}', expected_status=404)
        self.log_test("Delete Nonexistent Lesson", success, "- Expected 404 error")
        
        return True

    def run_delete_auth_tests(self):
        """Run all delete authentication tests"""
        print("🔐 Starting Delete Functionality Authentication Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Setup authentication
        print("\n📝 Authentication Setup:")
        if not self.test_user_registration_and_login():
            print("❌ Authentication setup failed. Cannot continue with delete tests.")
            return 1
            
        # Setup test data
        print("\n🏗️ Test Data Setup:")
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot continue with delete tests.")
            return 1
            
        # Delete tests with valid authentication
        print("\n✅ Delete Tests with Valid Authentication:")
        self.test_delete_teacher_with_valid_auth()
        self.test_delete_student_with_valid_auth()
        self.test_delete_lesson_with_valid_auth()
        
        # Delete tests without authentication
        print("\n🚫 Delete Tests without Authentication:")
        self.test_delete_teacher_without_auth()
        self.test_delete_student_without_auth()
        self.test_delete_lesson_without_auth()
        
        # Delete tests with invalid authentication
        print("\n🔑 Delete Tests with Invalid Authentication:")
        self.test_delete_teacher_with_invalid_auth()
        self.test_delete_student_with_invalid_auth()
        self.test_delete_lesson_with_invalid_auth()
        
        # Delete tests for non-existent records
        print("\n🔍 Delete Tests for Non-existent Records:")
        self.test_delete_nonexistent_records()
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📊 Delete Authentication Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All delete authentication tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = DeleteAuthenticationTester()
    return tester.run_delete_auth_tests()

if __name__ == "__main__":
    sys.exit(main())