import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class DanceStudioAPITester:
    def __init__(self, base_url="https://b2502ddb-b963-47af-bb92-eb4f1e53e4fb.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_teacher_id = None
        self.created_class_id = None

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
            required_fields = ['total_classes', 'total_teachers', 'classes_today']
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

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Dance Studio API Tests")
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
        
        # Class management tests
        print("\n💃 Class Management Tests:")
        self.test_create_class()
        self.test_get_classes()
        self.test_get_class_by_id()
        self.test_update_class()
        
        # Calendar tests
        print("\n📅 Calendar Tests:")
        self.test_weekly_calendar()
        
        # Cleanup tests
        print("\n🧹 Cleanup Tests:")
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