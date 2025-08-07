#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class DanceProgramTester:
    def __init__(self, base_url="https://40cca8f8-7cce-4162-b27d-7b2165da8a53.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_student_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data=None, expected_status: int = 200):
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

    def setup_auth(self):
        """Setup authentication for testing"""
        # Register a test user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"test_dance_programs_{timestamp}@example.com",
            "name": f"Dance Program Tester {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success:
            self.user_id = response.get('id')
            self.test_email = user_data['email']
            self.test_password = user_data['password']
            
            # Login
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            success, login_response = self.make_request('POST', 'auth/login', login_data, 200)
            
            if success:
                self.token = login_response.get('access_token')
                
        self.log_test("Authentication Setup", success, f"- Token: {'Yes' if self.token else 'No'}")
        return success

    def test_get_programs(self):
        """Test getting all dance programs"""
        success, response = self.make_request('GET', 'programs', expected_status=200)
        
        if success:
            programs_count = len(response) if isinstance(response, list) else 0
            # Should have 12 default programs
            expected_programs = [
                "Beginner Program", "Social Foundation", "Newcomers Bronze", 
                "Beginner Bronze", "Intermediate Bronze", "Full Bronze",
                "Beginner Silver", "Intermediate Silver", "Full Silver",
                "Beginner Gold", "Intermediate Gold", "Full Gold"
            ]
            
            program_names = [p.get('name', '') for p in response] if isinstance(response, list) else []
            has_expected_programs = all(name in program_names for name in expected_programs)
            
            success = success and programs_count >= 12 and has_expected_programs
            
            print(f"   Found programs: {program_names}")
            
        self.log_test("Get Dance Programs", success, f"- Found {programs_count} programs (expected 12+)")
        return success

    def test_get_program_by_id(self):
        """Test getting a specific dance program"""
        # First get all programs to get an ID
        success, programs = self.make_request('GET', 'programs', expected_status=200)
        if not success or not programs:
            self.log_test("Get Program by ID", False, "- No programs available")
            return False
            
        program_id = programs[0].get('id')
        success, response = self.make_request('GET', f'programs/{program_id}', expected_status=200)
        
        program_name = "Unknown"
        program_level = "Unknown"
        if success:
            program_name = response.get('name', 'Unknown')
            program_level = response.get('level', 'Unknown')
            
        self.log_test("Get Program by ID", success, f"- Program: {program_name} ({program_level})")
        return success

    def test_programs_startup_creation(self):
        """Test that default programs are created on startup"""
        success, response = self.make_request('GET', 'programs', expected_status=200)
        
        if success:
            programs_count = len(response) if isinstance(response, list) else 0
            
            # Check for specific program levels
            levels_found = set()
            for program in response:
                level = program.get('level', '')
                levels_found.add(level)
            
            expected_levels = {'Beginner', 'Social', 'Bronze', 'Silver', 'Gold'}
            has_all_levels = expected_levels.issubset(levels_found)
            
            success = success and programs_count >= 12 and has_all_levels
            
        self.log_test("Programs Startup Creation", success, 
                     f"- Found {programs_count} programs with levels: {sorted(levels_found)}")
        return success

    def setup_test_student(self):
        """Create a test student for enrollment testing"""
        student_data = {
            "name": "Dance Program Test Student",
            "email": "dance.program.test@example.com",
            "phone": "+1555123456",
            "parent_name": "Test Parent",
            "parent_phone": "+1555123457",
            "parent_email": "test.parent@example.com",
            "notes": "Student for dance program enrollment testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        
        if success:
            self.created_student_id = response.get('id')
            
        self.log_test("Setup Test Student", success, f"- Student ID: {self.created_student_id}")
        return success

    def test_create_enrollment_with_program(self):
        """Test creating enrollment with dance program name"""
        if not self.created_student_id:
            self.log_test("Create Enrollment with Program", False, "- No student ID available")
            return False
            
        # Get available programs first
        success, programs = self.make_request('GET', 'programs', expected_status=200)
        if not success or not programs:
            self.log_test("Create Enrollment with Program", False, "- No programs available")
            return False
            
        # Use the first program
        program = programs[0]
        enrollment_data = {
            "student_id": self.created_student_id,
            "program_name": program['name'],
            "total_lessons": 8,
            "total_paid": 400.0
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        
        program_name = "Unknown"
        total_lessons = 0
        remaining_lessons = 0
        if success:
            self.created_enrollment_id = response.get('id')
            program_name = response.get('program_name')
            total_lessons = response.get('total_lessons')
            remaining_lessons = response.get('remaining_lessons')
            
            # Verify remaining_lessons equals total_lessons on creation
            success = success and remaining_lessons == total_lessons
            
        self.log_test("Create Enrollment with Program", success, 
                     f"- Program: {program_name}, Lessons: {total_lessons}/{remaining_lessons}")
        return success

    def test_create_enrollment_custom_lessons(self):
        """Test creating enrollment with custom lesson numbers"""
        if not self.created_student_id:
            self.log_test("Create Enrollment Custom Lessons", False, "- No student ID available")
            return False
            
        # Get available programs
        success, programs = self.make_request('GET', 'programs', expected_status=200)
        if not success or not programs:
            self.log_test("Create Enrollment Custom Lessons", False, "- No programs available")
            return False
            
        # Test various custom lesson numbers
        test_cases = [
            {"lessons": 1, "paid": 50.0, "program": "Beginner Program"},
            {"lessons": 25, "paid": 1250.0, "program": "Intermediate Bronze"},
            {"lessons": 100, "paid": 4500.0, "program": "Full Gold"}
        ]
        
        successful_enrollments = 0
        
        for case in test_cases:
            enrollment_data = {
                "student_id": self.created_student_id,
                "program_name": case["program"],
                "total_lessons": case["lessons"],
                "total_paid": case["paid"]
            }
            
            success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
            
            if success:
                total_lessons = response.get('total_lessons')
                remaining_lessons = response.get('remaining_lessons')
                
                if total_lessons == case["lessons"] and remaining_lessons == case["lessons"]:
                    successful_enrollments += 1
                    print(f"   ✅ {case['lessons']} lessons enrollment created successfully")
                else:
                    print(f"   ❌ Lesson count mismatch for {case['lessons']} lessons")
            else:
                print(f"   ❌ Failed to create enrollment with {case['lessons']} lessons")
        
        success = successful_enrollments == len(test_cases)
        self.log_test("Create Enrollment Custom Lessons", success, 
                     f"- {successful_enrollments}/{len(test_cases)} custom enrollments created")
        return success

    def test_enrollment_program_validation(self):
        """Test enrollment validation with invalid program names"""
        if not self.created_student_id:
            self.log_test("Enrollment Program Validation", False, "- No student ID available")
            return False
            
        # Test with invalid program name
        enrollment_data = {
            "student_id": self.created_student_id,
            "program_name": "Non-existent Program",
            "total_lessons": 10,
            "total_paid": 500.0
        }
        
        # This should still succeed as we don't validate program names against existing programs
        # The system allows any program name for flexibility
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        
        program_name = "Unknown"
        if success:
            program_name = response.get('program_name')
            
        self.log_test("Enrollment Program Validation", success, 
                     f"- Accepts any program name: {program_name}")
        return success

    def test_get_enrollments(self):
        """Test getting all enrollments"""
        success, response = self.make_request('GET', 'enrollments', expected_status=200)
        
        enrollments_count = 0
        if success:
            enrollments_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Enrollments", success, f"- Found {enrollments_count} enrollments")
        return success

    def test_get_student_enrollments(self):
        """Test getting student's enrollments"""
        if not self.created_student_id:
            self.log_test("Get Student Enrollments", False, "- No student ID available")
            return False
            
        success, response = self.make_request('GET', f'students/{self.created_student_id}/enrollments', expected_status=200)
        
        enrollments_count = 0
        if success:
            enrollments_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Student Enrollments", success, f"- Found {enrollments_count} enrollments for student")
        return success

    def test_lesson_attendance_deduction(self):
        """Test that lesson attendance deducts from remaining lessons"""
        if not self.created_student_id or not hasattr(self, 'created_enrollment_id'):
            self.log_test("Lesson Attendance Deduction", False, "- No student or enrollment ID available")
            return False
            
        # Create a teacher first
        teacher_data = {
            "name": "Test Teacher",
            "email": "test.teacher@example.com",
            "phone": "+1555987654",
            "specialties": ["ballet"],
            "bio": "Test teacher for lesson attendance"
        }
        
        success, teacher_response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Lesson Attendance Deduction", False, "- Failed to create test teacher")
            return False
            
        teacher_id = teacher_response.get('id')
        
        # Create a lesson
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_id": teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Test lesson for attendance deduction",
            "enrollment_id": self.created_enrollment_id
        }
        
        success, lesson_response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Lesson Attendance Deduction", False, "- Failed to create test lesson")
            return False
            
        lesson_id = lesson_response.get('id')
        
        # Get enrollment before attendance
        success, enrollment_before = self.make_request('GET', f'students/{self.created_student_id}/enrollments', expected_status=200)
        if not success:
            self.log_test("Lesson Attendance Deduction", False, "- Failed to get enrollment before attendance")
            return False
            
        remaining_before = enrollment_before[0].get('remaining_lessons', 0) if enrollment_before else 0
        
        # Mark lesson as attended
        success, attend_response = self.make_request('POST', f'lessons/{lesson_id}/attend', expected_status=200)
        if not success:
            self.log_test("Lesson Attendance Deduction", False, "- Failed to mark lesson attended")
            return False
            
        # Get enrollment after attendance
        success, enrollment_after = self.make_request('GET', f'students/{self.created_student_id}/enrollments', expected_status=200)
        if not success:
            self.log_test("Lesson Attendance Deduction", False, "- Failed to get enrollment after attendance")
            return False
            
        remaining_after = enrollment_after[0].get('remaining_lessons', 0) if enrollment_after else 0
        
        # Verify lesson was deducted
        success = remaining_after == (remaining_before - 1)
        
        self.log_test("Lesson Attendance Deduction", success, 
                     f"- Lessons: {remaining_before} → {remaining_after} (deducted: {remaining_before - remaining_after})")
        return success

    def run_all_tests(self):
        """Run all dance program tests"""
        print("🎭 Starting Dance Program Enrollment System Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Setup
        print("\n🔧 Setup:")
        if not self.setup_auth():
            print("❌ Authentication setup failed, aborting tests")
            return 1
            
        if not self.setup_test_student():
            print("❌ Test student setup failed, aborting tests")
            return 1
        
        # Dance Programs API Tests
        print("\n🎭 Dance Programs API Tests:")
        self.test_get_programs()
        self.test_get_program_by_id()
        self.test_programs_startup_creation()
        
        # Enhanced Enrollment System Tests
        print("\n📋 Enhanced Enrollment System Tests:")
        self.test_create_enrollment_with_program()
        self.test_create_enrollment_custom_lessons()
        self.test_enrollment_program_validation()
        self.test_get_enrollments()
        self.test_get_student_enrollments()
        
        # Integration Tests
        print("\n🔗 Integration Tests:")
        self.test_lesson_attendance_deduction()
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All dance program tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = DanceProgramTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())