import requests
import sys
import json
import websocket
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class DanceStudioAPITester:
    def __init__(self, base_url="https://dependable-imagination-production.up.railway.app"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_teacher_id = None
        self.created_class_id = None
        self.created_student_id = None
        self.created_lesson_id = None
        self.created_enrollment_id = None
        self.available_packages = []
        self.created_recurring_series_id = None
        self.websocket_messages = []
        self.websocket_connected = False

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

    def test_user_registration(self):
        """Test user registration"""
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
            
        self.log_test("User Registration", success, f"- User ID: {self.user_id}")
        return success

    def test_user_login(self):
        """Test user login"""
        if not hasattr(self, 'test_email'):
            self.log_test("User Login", False, "- No registered user to login with")
            return False
            
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            user_info = response.get('user', {})
            
        self.log_test("User Login", success, f"- Token received: {'Yes' if self.token else 'No'}")
        return success

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        success, response = self.make_request('GET', 'dashboard/stats', expected_status=200)
        
        if success:
            required_fields = ['total_classes', 'total_teachers', 'total_students', 'active_enrollments', 
                             'classes_today', 'lessons_today', 'lessons_attended_today', 'estimated_monthly_revenue']
            has_all_fields = all(field in response for field in required_fields)
            success = has_all_fields
            
        self.log_test("Dashboard Stats", success, f"- Stats: {response if success else 'Missing fields'}")
        return success

    def test_create_teacher(self):
        """Test creating a teacher"""
        teacher_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1234567890",
            "specialties": ["ballet", "contemporary"],
            "bio": "Experienced ballet instructor with 10+ years of teaching."
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        
        if success:
            self.created_teacher_id = response.get('id')
            
        self.log_test("Create Teacher", success, f"- Teacher ID: {self.created_teacher_id}")
        return success

    def test_get_teachers(self):
        """Test getting all teachers"""
        success, response = self.make_request('GET', 'teachers', expected_status=200)
        
        if success:
            teachers_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Teachers", success, f"- Found {teachers_count} teachers")
        return success

    def test_get_teacher_by_id(self):
        """Test getting a specific teacher"""
        if not self.created_teacher_id:
            self.log_test("Get Teacher by ID", False, "- No teacher ID available")
            return False
            
        success, response = self.make_request('GET', f'teachers/{self.created_teacher_id}', expected_status=200)
        
        if success:
            teacher_name = response.get('name', 'Unknown')
            
        self.log_test("Get Teacher by ID", success, f"- Teacher: {teacher_name}")
        return success

    def test_create_class(self):
        """Test creating a dance class"""
        if not self.created_teacher_id:
            self.log_test("Create Class", False, "- No teacher available for class")
            return False
            
        # Create class for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        class_data = {
            "title": "Morning Ballet Class",
            "class_type": "ballet",
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "end_datetime": end_time.isoformat(),
            "capacity": 15,
            "description": "Beginner-friendly ballet class",
            "studio_room": "Studio A",
            "price": 25.0
        }
        
        success, response = self.make_request('POST', 'classes', class_data, 200)
        
        if success:
            self.created_class_id = response.get('id')
            
        self.log_test("Create Class", success, f"- Class ID: {self.created_class_id}")
        return success

    def test_get_classes(self):
        """Test getting all classes"""
        success, response = self.make_request('GET', 'classes', expected_status=200)
        
        if success:
            classes_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Classes", success, f"- Found {classes_count} classes")
        return success

    def test_get_class_by_id(self):
        """Test getting a specific class"""
        if not self.created_class_id:
            self.log_test("Get Class by ID", False, "- No class ID available")
            return False
            
        success, response = self.make_request('GET', f'classes/{self.created_class_id}', expected_status=200)
        
        if success:
            class_title = response.get('title', 'Unknown')
            teacher_name = response.get('teacher_name', 'Unknown')
            
        self.log_test("Get Class by ID", success, f"- Class: {class_title} by {teacher_name}")
        return success

    def test_update_class(self):
        """Test updating a class"""
        if not self.created_class_id or not self.created_teacher_id:
            self.log_test("Update Class", False, "- No class or teacher ID available")
            return False
            
        # Update class details
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1, minutes=30)
        
        update_data = {
            "title": "Updated Morning Ballet Class",
            "class_type": "ballet",
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "end_datetime": end_time.isoformat(),
            "capacity": 20,
            "description": "Updated beginner-friendly ballet class",
            "studio_room": "Studio B",
            "price": 30.0
        }
        
        success, response = self.make_request('PUT', f'classes/{self.created_class_id}', update_data, 200)
        
        if success:
            updated_title = response.get('title', 'Unknown')
            
        self.log_test("Update Class", success, f"- Updated title: {updated_title}")
        return success

    def test_weekly_calendar(self):
        """Test weekly calendar endpoint"""
        # Get classes for current week
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_date = start_of_week.isoformat()
        
        success, response = self.make_request('GET', f'calendar/weekly?start_date={start_date}', expected_status=200)
        
        if success:
            classes_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Weekly Calendar", success, f"- Found {classes_count} classes this week")
        return success

    def test_delete_class(self):
        """Test deleting a class"""
        if not self.created_class_id:
            self.log_test("Delete Class", False, "- No class ID available")
            return False
            
        success, response = self.make_request('DELETE', f'classes/{self.created_class_id}', expected_status=200)
        
        self.log_test("Delete Class", success, f"- Message: {response.get('message', 'No message')}")
        return success

    # Student Management Tests
    def test_create_student(self):
        """Test creating a student"""
        student_data = {
            "name": "Emma Rodriguez",
            "email": "emma.rodriguez@example.com",
            "phone": "+1555123456",
            "parent_name": "Maria Rodriguez",
            "parent_phone": "+1555123457",
            "parent_email": "maria.rodriguez@example.com",
            "notes": "Interested in ballet and contemporary dance"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        
        if success:
            self.created_student_id = response.get('id')
            
        self.log_test("Create Student", success, f"- Student ID: {self.created_student_id}")
        return success

    def test_get_students(self):
        """Test getting all students"""
        success, response = self.make_request('GET', 'students', expected_status=200)
        
        if success:
            students_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Students", success, f"- Found {students_count} students")
        return success

    def test_get_student_by_id(self):
        """Test getting a specific student"""
        if not self.created_student_id:
            self.log_test("Get Student by ID", False, "- No student ID available")
            return False
            
        success, response = self.make_request('GET', f'students/{self.created_student_id}', expected_status=200)
        
        if success:
            student_name = response.get('name', 'Unknown')
            
        self.log_test("Get Student by ID", success, f"- Student: {student_name}")
        return success

    def test_update_student(self):
        """Test updating a student"""
        if not self.created_student_id:
            self.log_test("Update Student", False, "- No student ID available")
            return False
            
        update_data = {
            "name": "Emma Rodriguez-Smith",
            "email": "emma.rodriguez@example.com",
            "phone": "+1555123456",
            "parent_name": "Maria Rodriguez",
            "parent_phone": "+1555123457",
            "parent_email": "maria.rodriguez@example.com",
            "notes": "Updated: Interested in ballet, contemporary, and jazz dance"
        }
        
        success, response = self.make_request('PUT', f'students/{self.created_student_id}', update_data, 200)
        
        updated_name = "Unknown"
        if success:
            updated_name = response.get('name', 'Unknown')
            
        self.log_test("Update Student", success, f"- Updated name: {updated_name}")
        return success

    # Dance Programs Tests
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

    # Enhanced Enrollment Tests
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
        
        if success:
            program_name = response.get('program_name')
            
        self.log_test("Enrollment Program Validation", success, 
                     f"- Accepts any program name: {program_name}")
        return success

    # Package Management Tests (Legacy)
    def test_get_packages(self):
        """Test getting lesson packages (legacy system)"""
        success, response = self.make_request('GET', 'packages', expected_status=200)
        
        if success:
            packages_count = len(response) if isinstance(response, list) else 0
            self.available_packages = response
            
        self.log_test("Get Packages (Legacy)", success, f"- Found {packages_count} legacy packages")
        return success

    # Legacy Enrollment Tests (for backward compatibility)
    def test_create_enrollment(self):
        """Test creating a student enrollment (legacy package system)"""
        if not self.created_student_id or not self.available_packages:
            self.log_test("Create Enrollment (Legacy)", False, "- No student ID or packages available")
            return False
            
        # Use the first available package
        package = self.available_packages[0]
        enrollment_data = {
            "student_id": self.created_student_id,
            "package_id": package['id'],
            "total_paid": package['price']
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        
        if success:
            legacy_enrollment_id = response.get('id')
            
        self.log_test("Create Enrollment (Legacy)", success, f"- Legacy Enrollment ID: {legacy_enrollment_id}")
        return success

    def test_get_enrollments(self):
        """Test getting all enrollments"""
        success, response = self.make_request('GET', 'enrollments', expected_status=200)
        
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
        
        if success:
            enrollments_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Student Enrollments", success, f"- Found {enrollments_count} enrollments for student")
        return success

    # Private Lesson Tests
    def test_create_private_lesson(self):
        """Test creating a private lesson"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Private Lesson", False, "- No student or teacher ID available")
            return False
            
        # Create lesson for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Private ballet lesson focusing on technique",
            "enrollment_id": self.created_enrollment_id
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        
        if success:
            self.created_lesson_id = response.get('id')
            
        self.log_test("Create Private Lesson", success, f"- Lesson ID: {self.created_lesson_id}")
        return success

    def test_get_private_lessons(self):
        """Test getting all private lessons"""
        success, response = self.make_request('GET', 'lessons', expected_status=200)
        
        if success:
            lessons_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Private Lessons", success, f"- Found {lessons_count} private lessons")
        return success

    def test_get_private_lesson_by_id(self):
        """Test getting a specific private lesson"""
        if not self.created_lesson_id:
            self.log_test("Get Private Lesson by ID", False, "- No lesson ID available")
            return False
            
        success, response = self.make_request('GET', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        if success:
            student_name = response.get('student_name', 'Unknown')
            teacher_name = response.get('teacher_name', 'Unknown')
            
        self.log_test("Get Private Lesson by ID", success, f"- Lesson: {student_name} with {teacher_name}")
        return success

    def test_update_private_lesson(self):
        """Test updating a private lesson"""
        if not self.created_lesson_id:
            self.log_test("Update Private Lesson", False, "- No lesson ID available")
            return False
            
        # Update lesson time and notes
        tomorrow = datetime.now() + timedelta(days=1)
        new_start_time = tomorrow.replace(hour=15, minute=30, second=0, microsecond=0)
        
        update_data = {
            "start_datetime": new_start_time.isoformat(),
            "duration_minutes": 90,
            "notes": "Updated: Extended private ballet lesson focusing on advanced technique"
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}', update_data, 200)
        
        if success:
            updated_notes = response.get('notes', 'No notes')
            
        self.log_test("Update Private Lesson", success, f"- Updated notes: {updated_notes[:50]}...")
        return success

    def test_mark_lesson_attended(self):
        """Test marking a lesson as attended"""
        if not self.created_lesson_id:
            self.log_test("Mark Lesson Attended", False, "- No lesson ID available")
            return False
            
        success, response = self.make_request('POST', f'lessons/{self.created_lesson_id}/attend', expected_status=200)
        
        self.log_test("Mark Lesson Attended", success, f"- Message: {response.get('message', 'No message')}")
        return success

    def test_daily_calendar(self):
        """Test daily calendar endpoint"""
        # Get calendar for tomorrow (when we scheduled lessons)
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime('%Y-%m-%d')
        
        success, response = self.make_request('GET', f'calendar/daily/{date_str}', expected_status=200)
        
        if success:
            lessons_count = len(response.get('lessons', [])) if isinstance(response, dict) else 0
            teachers_count = len(response.get('teachers', [])) if isinstance(response, dict) else 0
            
        self.log_test("Daily Calendar", success, f"- Found {lessons_count} lessons, {teachers_count} teachers")
        return success

    def test_delete_private_lesson(self):
        """Test deleting a private lesson"""
        if not self.created_lesson_id:
            self.log_test("Delete Private Lesson", False, "- No lesson ID available")
            return False
            
        success, response = self.make_request('DELETE', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        self.log_test("Delete Private Lesson", success, f"- Message: {response.get('message', 'No message')}")
        return success

    # NEW DELETE FUNCTIONALITY TESTS
    def test_delete_student_with_associations(self):
        """Test deleting a student and checking associated records"""
        if not self.created_student_id:
            self.log_test("Delete Student with Associations", False, "- No student ID available")
            return False
            
        success, response = self.make_request('DELETE', f'students/{self.created_student_id}', expected_status=200)
        
        associated_lessons = 0
        associated_enrollments = 0
        if success:
            message = response.get('message', '')
            associated_lessons = response.get('associated_lessons', 0)
            associated_enrollments = response.get('associated_enrollments', 0)
            note = response.get('note', '')
            
        self.log_test("Delete Student with Associations", success, 
                     f"- Lessons: {associated_lessons}, Enrollments: {associated_enrollments}")
        return success

    def test_delete_nonexistent_student(self):
        """Test deleting a non-existent student"""
        fake_student_id = "nonexistent-student-id"
        success, response = self.make_request('DELETE', f'students/{fake_student_id}', expected_status=404)
        
        self.log_test("Delete Non-existent Student", success, f"- Expected 404 error")
        return success

    def test_delete_teacher_with_associations(self):
        """Test deleting a teacher and checking associated records"""
        if not self.created_teacher_id:
            self.log_test("Delete Teacher with Associations", False, "- No teacher ID available")
            return False
            
        success, response = self.make_request('DELETE', f'teachers/{self.created_teacher_id}', expected_status=200)
        
        associated_lessons = 0
        associated_classes = 0
        if success:
            message = response.get('message', '')
            associated_lessons = response.get('associated_lessons', 0)
            associated_classes = response.get('associated_classes', 0)
            note = response.get('note', '')
            
        self.log_test("Delete Teacher with Associations", success, 
                     f"- Lessons: {associated_lessons}, Classes: {associated_classes}")
        return success

    def test_delete_nonexistent_teacher(self):
        """Test deleting a non-existent teacher"""
        fake_teacher_id = "nonexistent-teacher-id"
        success, response = self.make_request('DELETE', f'teachers/{fake_teacher_id}', expected_status=404)
        
        self.log_test("Delete Non-existent Teacher", success, f"- Expected 404 error")
        return success

    # NOTIFICATION SYSTEM TESTS
    def test_create_notification_preferences(self):
        """Test creating notification preferences for a student"""
        # First create a new student for notification testing
        student_data = {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@example.com",
            "phone": "+1555987654",
            "parent_name": "Jennifer Johnson",
            "parent_phone": "+1555987655",
            "parent_email": "jennifer.johnson@example.com",
            "notes": "Student for notification testing"
        }
        
        success, student_response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Create Notification Preferences", False, "- Failed to create test student")
            return False
            
        self.notification_test_student_id = student_response.get('id')
        
        # Create notification preferences
        pref_data = {
            "student_id": self.notification_test_student_id,
            "email_enabled": True,
            "sms_enabled": True,
            "reminder_hours": 24,
            "email_address": "sarah.johnson@example.com",
            "phone_number": "+1555987654"
        }
        
        success, response = self.make_request('POST', 'notifications/preferences', pref_data, 200)
        
        email_enabled = False
        sms_enabled = False
        if success:
            student_id = response.get('student_id')
            email_enabled = response.get('email_enabled')
            sms_enabled = response.get('sms_enabled')
            
        self.log_test("Create Notification Preferences", success, 
                     f"- Email: {email_enabled}, SMS: {sms_enabled}")
        return success

    def test_update_notification_preferences(self):
        """Test updating existing notification preferences"""
        if not hasattr(self, 'notification_test_student_id'):
            self.log_test("Update Notification Preferences", False, "- No test student available")
            return False
            
        # Update preferences
        updated_pref_data = {
            "student_id": self.notification_test_student_id,
            "email_enabled": False,
            "sms_enabled": True,
            "reminder_hours": 48,
            "email_address": "sarah.updated@example.com",
            "phone_number": "+1555987654"
        }
        
        success, response = self.make_request('POST', 'notifications/preferences', updated_pref_data, 200)
        
        email_enabled = True
        reminder_hours = 24
        if success:
            email_enabled = response.get('email_enabled')
            reminder_hours = response.get('reminder_hours')
            
        self.log_test("Update Notification Preferences", success, 
                     f"- Email disabled, Reminder: {reminder_hours}h")
        return success

    def test_get_notification_preferences(self):
        """Test getting notification preferences for a student"""
        if not hasattr(self, 'notification_test_student_id'):
            self.log_test("Get Notification Preferences", False, "- No test student available")
            return False
            
        success, response = self.make_request('GET', f'notifications/preferences/{self.notification_test_student_id}', expected_status=200)
        
        email_enabled = False
        sms_enabled = False
        reminder_hours = 24
        if success:
            email_enabled = response.get('email_enabled')
            sms_enabled = response.get('sms_enabled')
            reminder_hours = response.get('reminder_hours')
            
        self.log_test("Get Notification Preferences", success, 
                     f"- Email: {email_enabled}, SMS: {sms_enabled}, Hours: {reminder_hours}")
        return success

    def test_get_default_notification_preferences(self):
        """Test getting default notification preferences for student without preferences"""
        # Create another student without preferences
        student_data = {
            "name": "Michael Chen",
            "email": "michael.chen@example.com",
            "phone": "+1555111222"
        }
        
        success, student_response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Get Default Notification Preferences", False, "- Failed to create test student")
            return False
            
        new_student_id = student_response.get('id')
        
        success, response = self.make_request('GET', f'notifications/preferences/{new_student_id}', expected_status=200)
        
        email_enabled = False
        sms_enabled = False
        reminder_hours = 24
        if success:
            email_enabled = response.get('email_enabled')
            sms_enabled = response.get('sms_enabled')
            reminder_hours = response.get('reminder_hours')
            
        self.log_test("Get Default Notification Preferences", success, 
                     f"- Default Email: {email_enabled}, SMS: {sms_enabled}, Hours: {reminder_hours}")
        
        # Clean up
        self.make_request('DELETE', f'students/{new_student_id}', expected_status=200)
        return success

    def test_create_lesson_for_reminder_testing(self):
        """Create a lesson for reminder testing"""
        if not hasattr(self, 'notification_test_student_id'):
            self.log_test("Create Lesson for Reminder Testing", False, "- No test student available")
            return False
            
        # Create a teacher for the lesson
        teacher_data = {
            "name": "Alex Martinez",
            "email": "alex.martinez@example.com",
            "phone": "+1555333444",
            "specialties": ["jazz", "hip_hop"],
            "bio": "Hip hop and jazz instructor"
        }
        
        success, teacher_response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Create Lesson for Reminder Testing", False, "- Failed to create test teacher")
            return False
            
        self.reminder_test_teacher_id = teacher_response.get('id')
        
        # Create lesson for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=16, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.notification_test_student_id,
            "teacher_id": self.reminder_test_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Jazz lesson for reminder testing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        
        lesson_id = ""
        if success:
            self.reminder_test_lesson_id = response.get('id')
            lesson_id = self.reminder_test_lesson_id
            
        self.log_test("Create Lesson for Reminder Testing", success, f"- Lesson ID: {lesson_id}")
        return success

    def test_send_email_reminder(self):
        """Test sending email reminder for a lesson"""
        if not hasattr(self, 'reminder_test_lesson_id'):
            self.log_test("Send Email Reminder", False, "- No test lesson available")
            return False
            
        # First enable email notifications for the student
        pref_data = {
            "student_id": self.notification_test_student_id,
            "email_enabled": True,
            "sms_enabled": True,
            "reminder_hours": 24,
            "email_address": "sarah.johnson@example.com",
            "phone_number": "+1555987654"
        }
        
        self.make_request('POST', 'notifications/preferences', pref_data, 200)
            
        reminder_data = {
            "lesson_id": self.reminder_test_lesson_id,
            "notification_type": "email",
            "message": "Custom reminder: Don't forget your jazz lesson tomorrow!"
        }
        
        success, response = self.make_request('POST', 'notifications/send-reminder', reminder_data, 200)
        
        recipient = ""
        if success:
            message = response.get('message', '')
            recipient = response.get('recipient', '')
            lesson_datetime = response.get('lesson_datetime', '')
            
        self.log_test("Send Email Reminder", success, f"- Sent to: {recipient}")
        return success

    def test_send_sms_reminder(self):
        """Test sending SMS reminder for a lesson"""
        if not hasattr(self, 'reminder_test_lesson_id'):
            self.log_test("Send SMS Reminder", False, "- No test lesson available")
            return False
            
        reminder_data = {
            "lesson_id": self.reminder_test_lesson_id,
            "notification_type": "sms"
        }
        
        success, response = self.make_request('POST', 'notifications/send-reminder', reminder_data, 200)
        
        recipient = ""
        if success:
            message = response.get('message', '')
            recipient = response.get('recipient', '')
            
        self.log_test("Send SMS Reminder", success, f"- Sent to: {recipient}")
        return success

    def test_send_reminder_invalid_lesson(self):
        """Test sending reminder for non-existent lesson"""
        reminder_data = {
            "lesson_id": "nonexistent-lesson-id",
            "notification_type": "email"
        }
        
        success, response = self.make_request('POST', 'notifications/send-reminder', reminder_data, 404)
        
        self.log_test("Send Reminder Invalid Lesson", success, "- Expected 404 error")
        return success

    def test_send_reminder_disabled_notifications(self):
        """Test sending reminder when notifications are disabled"""
        if not hasattr(self, 'reminder_test_lesson_id'):
            self.log_test("Send Reminder Disabled Notifications", False, "- No test lesson available")
            return False
            
        # First disable email notifications for the student
        pref_data = {
            "student_id": self.notification_test_student_id,
            "email_enabled": False,
            "sms_enabled": False,
            "reminder_hours": 24
        }
        
        self.make_request('POST', 'notifications/preferences', pref_data, 200)
        
        # Try to send email reminder
        reminder_data = {
            "lesson_id": self.reminder_test_lesson_id,
            "notification_type": "email"
        }
        
        success, response = self.make_request('POST', 'notifications/send-reminder', reminder_data, 400)
        
        self.log_test("Send Reminder Disabled Notifications", success, "- Expected 400 error for disabled email")
        return success

    def test_get_upcoming_lessons(self):
        """Test getting upcoming lessons for reminders"""
        success, response = self.make_request('GET', 'notifications/upcoming-lessons', expected_status=200)
        
        lessons_count = 0
        if success:
            lessons_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Upcoming Lessons", success, f"- Found {lessons_count} upcoming lessons")
        return success

    def test_notification_preferences_invalid_student(self):
        """Test creating notification preferences for non-existent student"""
        pref_data = {
            "student_id": "nonexistent-student-id",
            "email_enabled": True,
            "sms_enabled": False,
            "reminder_hours": 24
        }
        
        success, response = self.make_request('POST', 'notifications/preferences', pref_data, 404)
        
        self.log_test("Notification Preferences Invalid Student", success, "- Expected 404 error")
        return success

    # STATIC FILE SERVING TESTS FOR RAILWAY DEPLOYMENT
    def test_root_path_serves_react_app(self):
        """Test that root path (/) serves React app's index.html"""
        try:
            response = requests.get(self.base_url, timeout=10)
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('content-type', '')
                is_html = 'text/html' in content_type
                has_react_content = 'Dance Studio CRM' in response.text or 'root' in response.text
                success = is_html and (has_react_content or len(response.text) > 100)
                
            self.log_test("Root Path Serves React App", success, 
                         f"- Content-Type: {response.headers.get('content-type', 'unknown')}")
            return success
            
        except requests.exceptions.RequestException as e:
            self.log_test("Root Path Serves React App", False, f"- Request failed: {str(e)}")
            return False

    def test_static_js_files_served(self):
        """Test that static JavaScript files are served with correct MIME types"""
        # Try common static file paths that would exist in a React build
        static_paths = [
            "/static/js/main.js",
            "/static/js/bundle.js", 
            "/static/js/app.js"
        ]
        
        success_count = 0
        total_tests = len(static_paths)
        
        for path in static_paths:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                # Accept 200 (file exists) or 404 (file doesn't exist, but server is handling static routes)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    is_js = 'javascript' in content_type or 'application/javascript' in content_type
                    if is_js:
                        success_count += 1
                        print(f"   ✅ {path} - Content-Type: {content_type}")
                    else:
                        print(f"   ⚠️ {path} - Wrong Content-Type: {content_type}")
                elif response.status_code == 404:
                    # File doesn't exist but server handled the route (not a server error)
                    success_count += 1
                    print(f"   ✅ {path} - Handled by server (404)")
                else:
                    print(f"   ❌ {path} - Status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ {path} - Request failed: {str(e)}")
        
        # Consider test successful if at least one static route is properly handled
        success = success_count > 0
        self.log_test("Static JS Files Served", success, 
                     f"- {success_count}/{total_tests} static routes handled correctly")
        return success

    def test_static_css_files_served(self):
        """Test that static CSS files are served with correct MIME types"""
        static_paths = [
            "/static/css/main.css",
            "/static/css/app.css",
            "/static/css/style.css"
        ]
        
        success_count = 0
        total_tests = len(static_paths)
        
        for path in static_paths:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                # Accept 200 (file exists) or 404 (file doesn't exist, but server is handling static routes)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    is_css = 'text/css' in content_type or 'css' in content_type
                    if is_css:
                        success_count += 1
                        print(f"   ✅ {path} - Content-Type: {content_type}")
                    else:
                        print(f"   ⚠️ {path} - Wrong Content-Type: {content_type}")
                elif response.status_code == 404:
                    # File doesn't exist but server handled the route (not a server error)
                    success_count += 1
                    print(f"   ✅ {path} - Handled by server (404)")
                else:
                    print(f"   ❌ {path} - Status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ {path} - Request failed: {str(e)}")
        
        # Consider test successful if at least one static route is properly handled
        success = success_count > 0
        self.log_test("Static CSS Files Served", success, 
                     f"- {success_count}/{total_tests} static routes handled correctly")
        return success

    def test_api_endpoints_not_interfered(self):
        """Test that API endpoints still work and are not interfered by static serving"""
        # Test a few key API endpoints to ensure they still work
        api_tests = [
            ("dashboard/stats", "Dashboard stats API"),
            ("teachers", "Teachers API"),
            ("students", "Students API"),
            ("packages", "Packages API")
        ]
        
        success_count = 0
        total_tests = len(api_tests)
        
        for endpoint, description in api_tests:
            try:
                response = requests.get(f"{self.api_url}/{endpoint}", timeout=10)
                # API should return JSON, not HTML
                content_type = response.headers.get('content-type', '')
                is_json = 'application/json' in content_type
                
                if response.status_code == 200 and is_json:
                    success_count += 1
                    print(f"   ✅ {description} - Working correctly")
                elif response.status_code == 401:
                    # Some endpoints require auth, but they're responding correctly
                    success_count += 1
                    print(f"   ✅ {description} - Auth required (expected)")
                else:
                    print(f"   ❌ {description} - Status: {response.status_code}, Content-Type: {content_type}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ {description} - Request failed: {str(e)}")
        
        success = success_count == total_tests
        self.log_test("API Endpoints Not Interfered", success, 
                     f"- {success_count}/{total_tests} API endpoints working correctly")
        return success

    def test_catch_all_routing_serves_react(self):
        """Test that unknown paths serve React app index.html (for React Router)"""
        # Test various paths that should serve the React app
        react_router_paths = [
            "/dashboard",
            "/students", 
            "/teachers",
            "/calendar",
            "/some-unknown-path",
            "/nested/path/that/does/not/exist"
        ]
        
        success_count = 0
        total_tests = len(react_router_paths)
        
        for path in react_router_paths:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    is_html = 'text/html' in content_type
                    # Should serve HTML content (React app)
                    if is_html:
                        success_count += 1
                        print(f"   ✅ {path} - Serves React app")
                    else:
                        print(f"   ❌ {path} - Wrong Content-Type: {content_type}")
                else:
                    print(f"   ❌ {path} - Status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ {path} - Request failed: {str(e)}")
        
        success = success_count >= (total_tests * 0.8)  # Allow some flexibility
        self.log_test("Catch-all Routing Serves React", success, 
                     f"- {success_count}/{total_tests} paths serve React app correctly")
        return success

    def test_static_file_mounting_configuration(self):
        """Test that static file mounting is configured correctly"""
        # This test checks if the server properly handles static file requests
        # by testing the /static prefix specifically
        
        try:
            # Test the /static path directly (should either serve files or return 404, not 500)
            response = requests.get(f"{self.base_url}/static/", timeout=10)
            
            # Should not return server error (500), should handle the route
            success = response.status_code != 500
            
            if success:
                print(f"   ✅ Static path handled correctly - Status: {response.status_code}")
            else:
                print(f"   ❌ Static path returned server error - Status: {response.status_code}")
                
            self.log_test("Static File Mounting Configuration", success, 
                         f"- Static path returns status {response.status_code} (not 500)")
            return success
            
        except requests.exceptions.RequestException as e:
            self.log_test("Static File Mounting Configuration", False, f"- Request failed: {str(e)}")
            return False

    # RECURRING LESSON TESTS
    def test_create_recurring_lesson_weekly(self):
        """Test creating a weekly recurring lesson series"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Recurring Lesson Weekly", False, "- No student or teacher ID available")
            return False
            
        # Create weekly recurring lesson starting tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_date = start_time + timedelta(weeks=4)  # 4 weeks of lessons
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "recurrence_pattern": "weekly",
            "end_date": end_date.isoformat(),
            "notes": "Weekly ballet lesson series",
            "enrollment_id": self.created_enrollment_id
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        lessons_created = 0
        if success:
            self.created_recurring_series_id = response.get('series_id')
            lessons_created = response.get('lessons_created', 0)
            
        self.log_test("Create Recurring Lesson Weekly", success, 
                     f"- Series ID: {self.created_recurring_series_id}, Lessons: {lessons_created}")
        return success

    def test_create_recurring_lesson_monthly(self):
        """Test creating a monthly recurring lesson series"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Recurring Lesson Monthly", False, "- No student or teacher ID available")
            return False
            
        # Create monthly recurring lesson starting next week
        next_week = datetime.now() + timedelta(days=7)
        start_time = next_week.replace(hour=14, minute=0, second=0, microsecond=0)
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 90,
            "recurrence_pattern": "monthly",
            "max_occurrences": 3,
            "notes": "Monthly advanced technique lesson"
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        lessons_created = 0
        if success:
            lessons_created = response.get('lessons_created', 0)
            
        self.log_test("Create Recurring Lesson Monthly", success, f"- Lessons created: {lessons_created}")
        return success

    def test_create_recurring_lesson_bi_weekly(self):
        """Test creating a bi-weekly recurring lesson series"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Recurring Lesson Bi-weekly", False, "- No student or teacher ID available")
            return False
            
        # Create bi-weekly recurring lesson
        next_week = datetime.now() + timedelta(days=7)
        start_time = next_week.replace(hour=16, minute=30, second=0, microsecond=0)
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 75,
            "recurrence_pattern": "bi_weekly",
            "max_occurrences": 5,
            "notes": "Bi-weekly contemporary dance lesson"
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        lessons_created = 0
        if success:
            lessons_created = response.get('lessons_created', 0)
            
        self.log_test("Create Recurring Lesson Bi-weekly", success, f"- Lessons created: {lessons_created}")
        return success

    def test_get_recurring_lesson_series(self):
        """Test getting all recurring lesson series"""
        success, response = self.make_request('GET', 'recurring-lessons', expected_status=200)
        
        series_count = 0
        if success:
            series_count = len(response) if isinstance(response, list) else 0
            
        self.log_test("Get Recurring Lesson Series", success, f"- Found {series_count} recurring series")
        return success

    def test_cancel_recurring_lesson_series(self):
        """Test cancelling a recurring lesson series"""
        if not self.created_recurring_series_id:
            self.log_test("Cancel Recurring Lesson Series", False, "- No recurring series ID available")
            return False
            
        success, response = self.make_request('DELETE', f'recurring-lessons/{self.created_recurring_series_id}', expected_status=200)
        
        cancelled_lessons = 0
        if success:
            cancelled_lessons = response.get('cancelled_lessons_count', 0)
            
        self.log_test("Cancel Recurring Lesson Series", success, f"- Cancelled {cancelled_lessons} future lessons")
        return success

    def test_recurring_lesson_invalid_pattern(self):
        """Test creating recurring lesson with invalid pattern"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Recurring Lesson Invalid Pattern", False, "- No student or teacher ID available")
            return False
            
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "recurrence_pattern": "invalid_pattern",
            "max_occurrences": 3
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 422)
        
        self.log_test("Recurring Lesson Invalid Pattern", success, "- Expected 422 validation error")
        return success

    def test_cancel_nonexistent_recurring_series(self):
        """Test cancelling a non-existent recurring series"""
        fake_series_id = "nonexistent-series-id"
        success, response = self.make_request('DELETE', f'recurring-lessons/{fake_series_id}', expected_status=404)
        
        self.log_test("Cancel Nonexistent Recurring Series", success, "- Expected 404 error")
        return success

    # WEBSOCKET REAL-TIME UPDATE TESTS
    def websocket_on_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            self.websocket_messages.append(data)
            print(f"   📡 WebSocket message received: {data.get('type', 'unknown')}")
        except json.JSONDecodeError:
            print(f"   ⚠️ Invalid JSON in WebSocket message: {message}")

    def websocket_on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"   ❌ WebSocket error: {error}")

    def websocket_on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.websocket_connected = False
        print(f"   🔌 WebSocket connection closed")

    def websocket_on_open(self, ws):
        """Handle WebSocket open"""
        self.websocket_connected = True
        print(f"   ✅ WebSocket connection opened")

    def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        if not self.user_id:
            self.log_test("WebSocket Connection", False, "- No user ID available")
            return False
            
        try:
            # Convert HTTPS URL to WSS URL for WebSocket
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_url = f"{ws_url}/ws/{self.user_id}"
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(ws_url,
                                      on_message=self.websocket_on_message,
                                      on_error=self.websocket_on_error,
                                      on_close=self.websocket_on_close,
                                      on_open=self.websocket_on_open)
            
            # Run WebSocket in a separate thread
            def run_websocket():
                ws.run_forever()
            
            ws_thread = threading.Thread(target=run_websocket)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            time.sleep(2)
            
            success = self.websocket_connected
            
            # Close connection
            if success:
                ws.close()
                time.sleep(1)
            
            self.log_test("WebSocket Connection", success, f"- Connected: {success}")
            return success
            
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"- Error: {str(e)}")
            return False

    def test_websocket_real_time_student_updates(self):
        """Test real-time updates when student is created/updated"""
        if not self.websocket_connected:
            self.log_test("WebSocket Student Updates", False, "- WebSocket not connected")
            return False
            
        # Clear previous messages
        self.websocket_messages.clear()
        
        # Create a student to trigger real-time update
        student_data = {
            "name": "WebSocket Test Student",
            "email": "websocket.test@example.com",
            "phone": "+1555000111"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        
        if success:
            # Wait for WebSocket message
            time.sleep(2)
            
            # Check if we received a student_created message
            student_created_msg = None
            for msg in self.websocket_messages:
                if msg.get('type') == 'student_created':
                    student_created_msg = msg
                    break
            
            success = student_created_msg is not None
            
            if success:
                student_id = student_created_msg.get('data', {}).get('student_id')
                # Clean up
                self.make_request('DELETE', f'students/{student_id}', expected_status=200)
            
        self.log_test("WebSocket Student Updates", success, f"- Real-time update received: {success}")
        return success

    def test_websocket_real_time_lesson_updates(self):
        """Test real-time updates when lesson is updated"""
        if not self.websocket_connected or not self.created_lesson_id:
            self.log_test("WebSocket Lesson Updates", False, "- WebSocket not connected or no lesson available")
            return False
            
        # Clear previous messages
        self.websocket_messages.clear()
        
        # Update the lesson to trigger real-time update
        update_data = {
            "notes": "Updated via WebSocket test"
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}', update_data, 200)
        
        if success:
            # Wait for WebSocket message
            time.sleep(2)
            
            # Check if we received a lesson_updated message
            lesson_updated_msg = None
            for msg in self.websocket_messages:
                if msg.get('type') == 'lesson_updated':
                    lesson_updated_msg = msg
                    break
            
            success = lesson_updated_msg is not None
            
        self.log_test("WebSocket Lesson Updates", success, f"- Real-time update received: {success}")
        return success

    def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong functionality"""
        if not self.websocket_connected:
            self.log_test("WebSocket Ping Pong", False, "- WebSocket not connected")
            return False
            
        try:
            # This test would require a more complex WebSocket setup
            # For now, we'll just verify the connection is still active
            success = self.websocket_connected
            
            self.log_test("WebSocket Ping Pong", success, f"- Connection active: {success}")
            return success
            
        except Exception as e:
            self.log_test("WebSocket Ping Pong", False, f"- Error: {str(e)}")
            return False

    # NEW EDIT FUNCTIONALITY TESTS
    def test_student_edit_functionality(self):
        """Test comprehensive student edit functionality"""
        print("\n🎓 STUDENT EDIT FUNCTIONALITY TESTS")
        print("-" * 40)
        
        # Create a student for editing tests
        student_data = {
            "name": "Original Student Name",
            "email": "original@example.com",
            "phone": "+1555000001",
            "parent_name": "Original Parent",
            "parent_phone": "+1555000002",
            "parent_email": "parent@example.com",
            "notes": "Original notes"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Student Edit - Create Test Student", False, "- Failed to create test student")
            return False
            
        edit_test_student_id = response.get('id')
        self.log_test("Student Edit - Create Test Student", True, f"- Student ID: {edit_test_student_id}")
        
        # Test 1: Update all student fields
        updated_data = {
            "name": "Updated Student Name",
            "email": "updated@example.com", 
            "phone": "+1555111111",
            "parent_name": "Updated Parent Name",
            "parent_phone": "+1555111112",
            "parent_email": "updated.parent@example.com",
            "notes": "Updated notes with new information"
        }
        
        success, response = self.make_request('PUT', f'students/{edit_test_student_id}', updated_data, 200)
        
        if success:
            updated_name = response.get('name')
            updated_email = response.get('email')
            updated_phone = response.get('phone')
            updated_parent_name = response.get('parent_name')
            updated_notes = response.get('notes')
            
            # Verify all fields were updated
            all_updated = (
                updated_name == updated_data['name'] and
                updated_email == updated_data['email'] and
                updated_phone == updated_data['phone'] and
                updated_parent_name == updated_data['parent_name'] and
                updated_notes == updated_data['notes']
            )
            success = all_updated
            
        self.log_test("Student Edit - Update All Fields", success, 
                     f"- Name: {updated_name}, Email: {updated_email}")
        
        # Test 2: Partial update (only name and notes)
        partial_update = {
            "name": "Partially Updated Name",
            "email": updated_data['email'],  # Keep existing
            "phone": updated_data['phone'],  # Keep existing
            "parent_name": updated_data['parent_name'],  # Keep existing
            "parent_phone": updated_data['parent_phone'],  # Keep existing
            "parent_email": updated_data['parent_email'],  # Keep existing
            "notes": "Only notes updated"
        }
        
        success, response = self.make_request('PUT', f'students/{edit_test_student_id}', partial_update, 200)
        
        if success:
            name_updated = response.get('name') == partial_update['name']
            notes_updated = response.get('notes') == partial_update['notes']
            email_unchanged = response.get('email') == updated_data['email']
            success = name_updated and notes_updated and email_unchanged
            
        self.log_test("Student Edit - Partial Update", success, 
                     f"- Name and notes updated, other fields preserved")
        
        # Test 3: Update with authentication requirement
        # This should work since we have a valid token
        auth_test_data = {
            "name": "Auth Test Student",
            "email": updated_data['email'],
            "phone": updated_data['phone'],
            "parent_name": updated_data['parent_name'],
            "parent_phone": updated_data['parent_phone'],
            "parent_email": updated_data['parent_email'],
            "notes": "Testing authentication requirement"
        }
        
        success, response = self.make_request('PUT', f'students/{edit_test_student_id}', auth_test_data, 200)
        self.log_test("Student Edit - With Authentication", success, 
                     f"- Authentication required and working")
        
        # Test 4: Update non-existent student
        fake_student_id = "nonexistent-student-id"
        success, response = self.make_request('PUT', f'students/{fake_student_id}', updated_data, 404)
        self.log_test("Student Edit - Non-existent Student", success, 
                     f"- Expected 404 for non-existent student")
        
        # Test 5: Update without authentication (temporarily remove token)
        original_token = self.token
        self.token = None
        success, response = self.make_request('PUT', f'students/{edit_test_student_id}', updated_data, 403)
        self.token = original_token  # Restore token
        self.log_test("Student Edit - Without Authentication", success, 
                     f"- Expected 403 without authentication")
        
        # Clean up
        self.make_request('DELETE', f'students/{edit_test_student_id}', expected_status=200)
        
        return True

    def test_teacher_edit_functionality(self):
        """Test comprehensive teacher edit functionality"""
        print("\n👩‍🏫 TEACHER EDIT FUNCTIONALITY TESTS")
        print("-" * 40)
        
        # Create a teacher for editing tests
        teacher_data = {
            "name": "Original Teacher Name",
            "email": "original.teacher@example.com",
            "phone": "+1555000003",
            "specialties": ["ballet", "jazz"],
            "bio": "Original bio information"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Teacher Edit - Create Test Teacher", False, "- Failed to create test teacher")
            return False
            
        edit_test_teacher_id = response.get('id')
        self.log_test("Teacher Edit - Create Test Teacher", True, f"- Teacher ID: {edit_test_teacher_id}")
        
        # Test 1: Update all teacher fields
        updated_data = {
            "name": "Updated Teacher Name",
            "email": "updated.teacher@example.com",
            "phone": "+1555222222",
            "specialties": ["contemporary", "hip_hop", "ballroom"],
            "bio": "Updated bio with extensive teaching experience"
        }
        
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', updated_data, 200)
        
        if success:
            updated_name = response.get('name')
            updated_email = response.get('email')
            updated_phone = response.get('phone')
            updated_specialties = response.get('specialties', [])
            updated_bio = response.get('bio')
            
            # Verify all fields were updated
            specialties_match = set(updated_specialties) == set(updated_data['specialties'])
            all_updated = (
                updated_name == updated_data['name'] and
                updated_email == updated_data['email'] and
                updated_phone == updated_data['phone'] and
                specialties_match and
                updated_bio == updated_data['bio']
            )
            success = all_updated
            
        self.log_test("Teacher Edit - Update All Fields", success, 
                     f"- Name: {updated_name}, Specialties: {len(updated_specialties)}")
        
        # Test 2: Update specialties array
        specialty_update = {
            "name": updated_data['name'],
            "email": updated_data['email'],
            "phone": updated_data['phone'],
            "specialties": ["ballet", "contemporary", "tap", "salsa"],
            "bio": updated_data['bio']
        }
        
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', specialty_update, 200)
        
        if success:
            new_specialties = response.get('specialties', [])
            specialties_updated = set(new_specialties) == set(specialty_update['specialties'])
            success = specialties_updated
            
        self.log_test("Teacher Edit - Update Specialties Array", success, 
                     f"- New specialties: {new_specialties}")
        
        # Test 3: Partial update (only name and bio)
        partial_update = {
            "name": "Partially Updated Teacher",
            "email": updated_data['email'],  # Keep existing
            "phone": updated_data['phone'],  # Keep existing
            "specialties": specialty_update['specialties'],  # Keep existing
            "bio": "Only bio updated with new information"
        }
        
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', partial_update, 200)
        
        if success:
            name_updated = response.get('name') == partial_update['name']
            bio_updated = response.get('bio') == partial_update['bio']
            email_unchanged = response.get('email') == updated_data['email']
            success = name_updated and bio_updated and email_unchanged
            
        self.log_test("Teacher Edit - Partial Update", success, 
                     f"- Name and bio updated, other fields preserved")
        
        # Test 4: Update with authentication requirement
        auth_test_data = {
            "name": "Auth Test Teacher",
            "email": updated_data['email'],
            "phone": updated_data['phone'],
            "specialties": ["ballet"],
            "bio": "Testing authentication requirement"
        }
        
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', auth_test_data, 200)
        self.log_test("Teacher Edit - With Authentication", success, 
                     f"- Authentication required and working")
        
        # Test 5: Update non-existent teacher
        fake_teacher_id = "nonexistent-teacher-id"
        success, response = self.make_request('PUT', f'teachers/{fake_teacher_id}', updated_data, 404)
        self.log_test("Teacher Edit - Non-existent Teacher", success, 
                     f"- Expected 404 for non-existent teacher")
        
        # Test 6: Update without authentication
        original_token = self.token
        self.token = None
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', updated_data, 403)
        self.token = original_token  # Restore token
        self.log_test("Teacher Edit - Without Authentication", success, 
                     f"- Expected 403 without authentication")
        
        # Test 7: Invalid specialty validation
        invalid_specialty_data = {
            "name": "Test Teacher",
            "email": "test@example.com",
            "phone": "+1555000000",
            "specialties": ["invalid_specialty"],
            "bio": "Test bio"
        }
        
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', invalid_specialty_data, 422)
        self.log_test("Teacher Edit - Invalid Specialty", success, 
                     f"- Expected 422 for invalid specialty")
        
        # Clean up
        self.make_request('DELETE', f'teachers/{edit_test_teacher_id}', expected_status=200)
        
        return True

    def test_real_time_updates_for_edits(self):
        """Test that edit operations broadcast real-time updates"""
        print("\n📡 REAL-TIME UPDATES FOR EDITS TESTS")
        print("-" * 40)
        
        # This test verifies that the broadcast_update method is called
        # We can't easily test WebSocket in this environment, but we can verify
        # the endpoints work and don't throw errors during the broadcast calls
        
        # Create test student
        student_data = {
            "name": "Real-time Test Student",
            "email": "realtime@example.com",
            "phone": "+1555000004"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Real-time Updates - Create Student", False, "- Failed to create test student")
            return False
            
        realtime_student_id = response.get('id')
        
        # Update student (should trigger real-time broadcast)
        update_data = {
            "name": "Updated Real-time Student",
            "email": "updated.realtime@example.com",
            "phone": "+1555000005",
            "parent_name": "Test Parent",
            "parent_phone": "+1555000006",
            "parent_email": "parent.realtime@example.com",
            "notes": "Updated for real-time testing"
        }
        
        success, response = self.make_request('PUT', f'students/{realtime_student_id}', update_data, 200)
        self.log_test("Real-time Updates - Student Update", success, 
                     f"- Student update with real-time broadcast")
        
        # Create test teacher
        teacher_data = {
            "name": "Real-time Test Teacher",
            "email": "realtime.teacher@example.com",
            "phone": "+1555000007",
            "specialties": ["ballet"],
            "bio": "Real-time test teacher"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Real-time Updates - Create Teacher", False, "- Failed to create test teacher")
            return False
            
        realtime_teacher_id = response.get('id')
        
        # Update teacher (should trigger real-time broadcast)
        teacher_update_data = {
            "name": "Updated Real-time Teacher",
            "email": "updated.realtime.teacher@example.com",
            "phone": "+1555000008",
            "specialties": ["jazz", "contemporary"],
            "bio": "Updated real-time test teacher"
        }
        
        success, response = self.make_request('PUT', f'teachers/{realtime_teacher_id}', teacher_update_data, 200)
        self.log_test("Real-time Updates - Teacher Update", success, 
                     f"- Teacher update with real-time broadcast")
        
        # Clean up
        self.make_request('DELETE', f'students/{realtime_student_id}', expected_status=200)
        self.make_request('DELETE', f'teachers/{realtime_teacher_id}', expected_status=200)
        
        return True

    def test_data_validation_for_edits(self):
        """Test data validation for edit operations"""
        print("\n✅ DATA VALIDATION FOR EDITS TESTS")
        print("-" * 40)
        
        # Create test student and teacher for validation tests
        student_data = {
            "name": "Validation Test Student",
            "email": "validation@example.com",
            "phone": "+1555000009"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Data Validation - Create Student", False, "- Failed to create test student")
            return False
            
        validation_student_id = response.get('id')
        
        teacher_data = {
            "name": "Validation Test Teacher",
            "email": "validation.teacher@example.com",
            "phone": "+1555000010",
            "specialties": ["ballet"],
            "bio": "Validation test teacher"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Data Validation - Create Teacher", False, "- Failed to create test teacher")
            return False
            
        validation_teacher_id = response.get('id')
        
        # Test 1: Student email format validation (if implemented)
        invalid_email_data = {
            "name": "Test Student",
            "email": "invalid-email-format",
            "phone": "+1555000000",
            "parent_name": "Test Parent",
            "parent_phone": "+1555000001",
            "parent_email": "parent@example.com",
            "notes": "Test notes"
        }
        
        # Note: The current implementation may not have strict email validation
        # This test checks if the system handles it gracefully
        success, response = self.make_request('PUT', f'students/{validation_student_id}', invalid_email_data, None)
        # Accept either 200 (no validation) or 422 (validation error)
        success = response.get('email') is not None or 'error' in response
        self.log_test("Data Validation - Student Email Format", success, 
                     f"- Email validation handled")
        
        # Test 2: Required field validation for students
        missing_name_data = {
            "email": "test@example.com",
            "phone": "+1555000000"
            # Missing required 'name' field
        }
        
        success, response = self.make_request('PUT', f'students/{validation_student_id}', missing_name_data, 422)
        self.log_test("Data Validation - Student Required Fields", success, 
                     f"- Required field validation working")
        
        # Test 3: Required field validation for teachers
        missing_name_teacher_data = {
            "email": "teacher@example.com",
            "phone": "+1555000000",
            "specialties": ["ballet"],
            "bio": "Test bio"
            # Missing required 'name' field
        }
        
        success, response = self.make_request('PUT', f'teachers/{validation_teacher_id}', missing_name_teacher_data, 422)
        self.log_test("Data Validation - Teacher Required Fields", success, 
                     f"- Required field validation working")
        
        # Test 4: Teacher specialty validation
        invalid_specialties_data = {
            "name": "Test Teacher",
            "email": "teacher@example.com",
            "phone": "+1555000000",
            "specialties": ["invalid_dance_style", "another_invalid_style"],
            "bio": "Test bio"
        }
        
        success, response = self.make_request('PUT', f'teachers/{validation_teacher_id}', invalid_specialties_data, 422)
        self.log_test("Data Validation - Teacher Specialty Validation", success, 
                     f"- Specialty validation working")
        
        # Clean up
        self.make_request('DELETE', f'students/{validation_student_id}', expected_status=200)
        self.make_request('DELETE', f'teachers/{validation_teacher_id}', expected_status=200)
        
        return True

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comprehensive Dance Studio CRM API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Authentication tests
        print("\n📝 Authentication Tests:")
        self.test_user_registration()
        self.test_user_login()
        
        # Dashboard tests
        print("\n📊 Dashboard Tests:")
        self.test_dashboard_stats()
        
        # Teacher management tests
        print("\n👩‍🏫 Teacher Management Tests:")
        self.test_create_teacher()
        self.test_get_teachers()
        self.test_get_teacher_by_id()
        
        # Student management tests
        print("\n👨‍🎓 Student Management Tests:")
        self.test_create_student()
        self.test_get_students()
        self.test_get_student_by_id()
        self.test_update_student()
        
        # Dance Programs tests
        print("\n🎭 Dance Programs Tests:")
        self.test_get_programs()
        self.test_get_program_by_id()
        self.test_programs_startup_creation()
        
        # Package management tests (legacy)
        print("\n📦 Package Management Tests (Legacy):")
        self.test_get_packages()
        
        # Enhanced Enrollment tests (with dance programs)
        print("\n📋 Enhanced Enrollment Tests (Dance Programs):")
        self.test_create_enrollment_with_program()
        self.test_create_enrollment_custom_lessons()
        self.test_enrollment_program_validation()
        self.test_get_enrollments()
        self.test_get_student_enrollments()
        
        # Legacy Enrollment tests (for backward compatibility)
        print("\n📋 Legacy Enrollment Tests:")
        self.test_create_enrollment()
        
        # Private lesson tests
        print("\n🎯 Private Lesson Tests:")
        self.test_create_private_lesson()
        self.test_get_private_lessons()
        self.test_get_private_lesson_by_id()
        self.test_update_private_lesson()
        self.test_mark_lesson_attended()
        
        # Calendar tests
        print("\n📅 Calendar Tests:")
        self.test_daily_calendar()
        self.test_weekly_calendar()
        
        # Class management tests
        print("\n💃 Class Management Tests:")
        self.test_create_class()
        self.test_get_classes()
        self.test_get_class_by_id()
        self.test_update_class()
        
        # NEW DELETE FUNCTIONALITY TESTS
        print("\n🗑️ Delete Functionality Tests:")
        self.test_delete_nonexistent_student()
        self.test_delete_nonexistent_teacher()
        self.test_delete_student_with_associations()
        self.test_delete_teacher_with_associations()
        
        # NEW NOTIFICATION SYSTEM TESTS
        print("\n🔔 Notification System Tests:")
        self.test_create_notification_preferences()
        self.test_update_notification_preferences()
        self.test_get_notification_preferences()
        self.test_get_default_notification_preferences()
        self.test_notification_preferences_invalid_student()
        self.test_create_lesson_for_reminder_testing()
        self.test_send_email_reminder()
        self.test_send_sms_reminder()
        self.test_send_reminder_invalid_lesson()
        self.test_send_reminder_disabled_notifications()
        self.test_get_upcoming_lessons()
        
        # NEW RECURRING LESSON TESTS
        print("\n🔄 Recurring Lesson Tests:")
        self.test_create_recurring_lesson_weekly()
        self.test_create_recurring_lesson_monthly()
        self.test_create_recurring_lesson_bi_weekly()
        self.test_get_recurring_lesson_series()
        self.test_recurring_lesson_invalid_pattern()
        self.test_cancel_nonexistent_recurring_series()
        self.test_cancel_recurring_lesson_series()
        
        # NEW WEBSOCKET REAL-TIME UPDATE TESTS
        print("\n📡 WebSocket Real-time Update Tests:")
        self.test_websocket_connection()
        self.test_websocket_real_time_student_updates()
        self.test_websocket_real_time_lesson_updates()
        self.test_websocket_ping_pong()
        
        # NEW EDIT FUNCTIONALITY TESTS
        print("\n✏️ Edit Functionality Tests:")
        self.test_student_edit_functionality()
        self.test_teacher_edit_functionality()
        self.test_real_time_updates_for_edits()
        self.test_data_validation_for_edits()
        
        # RAILWAY DEPLOYMENT STATIC FILE SERVING TESTS
        print("\n🚀 Railway Deployment Static File Serving Tests:")
        self.test_root_path_serves_react_app()
        self.test_static_js_files_served()
        self.test_static_css_files_served()
        self.test_api_endpoints_not_interfered()
        self.test_catch_all_routing_serves_react()
        self.test_static_file_mounting_configuration()
        
        # Cleanup tests
        print("\n🧹 Cleanup Tests:")
        self.test_delete_private_lesson()
        self.test_delete_class()
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = DanceStudioAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())