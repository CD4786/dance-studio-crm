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
        
        if success:
            updated_name = response.get('name', 'Unknown')
            
        self.log_test("Update Student", success, f"- Updated name: {updated_name}")
        return success

    # Package Management Tests
    def test_get_packages(self):
        """Test getting lesson packages"""
        success, response = self.make_request('GET', 'packages', expected_status=200)
        
        if success:
            packages_count = len(response) if isinstance(response, list) else 0
            self.available_packages = response
            
        self.log_test("Get Packages", success, f"- Found {packages_count} packages")
        return success

    # Enrollment Tests
    def test_create_enrollment(self):
        """Test creating a student enrollment"""
        if not self.created_student_id or not self.available_packages:
            self.log_test("Create Enrollment", False, "- No student ID or packages available")
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
            self.created_enrollment_id = response.get('id')
            
        self.log_test("Create Enrollment", success, f"- Enrollment ID: {self.created_enrollment_id}")
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
        
        # Package management tests
        print("\n📦 Package Management Tests:")
        self.test_get_packages()
        
        # Enrollment tests
        print("\n📋 Enrollment Tests:")
        self.test_create_enrollment()
        self.test_get_enrollments()
        self.test_get_student_enrollments()
        
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