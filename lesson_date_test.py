import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class LessonDateHandlingTester:
    def __init__(self, base_url="https://dance-studio-crm.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_teacher_id = None
        self.created_student_id = None
        self.created_lessons = []

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

    def setup_test_data(self):
        """Setup test user, teacher, and student for testing"""
        print("🔧 Setting up test data...")
        
        # Register test user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"date_test_{timestamp}@example.com",
            "name": f"Date Test User {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Date Test Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        if not success:
            print("❌ Failed to register test user")
            return False
            
        # Login
        login_data = {
            "email": user_data['email'],
            "password": user_data['password']
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if not success:
            print("❌ Failed to login test user")
            return False
            
        self.token = response.get('access_token')
        
        # Create test teacher
        teacher_data = {
            "name": "Date Test Teacher",
            "email": "date.teacher@example.com",
            "phone": "+1555000001",
            "specialties": ["ballet", "jazz"],
            "bio": "Teacher for date testing"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            print("❌ Failed to create test teacher")
            return False
            
        self.created_teacher_id = response.get('id')
        
        # Create test student
        student_data = {
            "name": "Date Test Student",
            "email": "date.student@example.com",
            "phone": "+1555000002",
            "notes": "Student for date testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            print("❌ Failed to create test student")
            return False
            
        self.created_student_id = response.get('id')
        
        print(f"✅ Test data setup complete - Teacher: {self.created_teacher_id}, Student: {self.created_student_id}")
        return True

    def test_lesson_creation_specific_dates(self):
        """Test creating lessons for specific dates and verify they appear on correct days"""
        print("\n📅 Testing lesson creation for specific dates...")
        
        # Test multiple specific dates
        test_dates = [
            datetime.now() + timedelta(days=1),  # Tomorrow
            datetime.now() + timedelta(days=3),  # 3 days from now
            datetime.now() + timedelta(days=7),  # 1 week from now
            datetime.now() + timedelta(days=14), # 2 weeks from now
        ]
        
        successful_lessons = 0
        
        for i, test_date in enumerate(test_dates):
            # Set specific time: 2:00 PM
            lesson_datetime = test_date.replace(hour=14, minute=0, second=0, microsecond=0)
            
            print(f"   📍 Creating lesson for: {lesson_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            lesson_data = {
                "student_id": self.created_student_id,
                "teacher_id": self.created_teacher_id,
                "start_datetime": lesson_datetime.strftime('%Y-%m-%dT%H:%M'),  # Local time format
                "duration_minutes": 60,
                "notes": f"Date test lesson #{i+1} - should be on {lesson_datetime.strftime('%Y-%m-%d at %H:%M')}"
            }
            
            success, response = self.make_request('POST', 'lessons', lesson_data, 200)
            
            if success:
                lesson_id = response.get('id')
                returned_datetime = response.get('start_datetime')
                
                # Parse returned datetime and verify it matches our intended date
                if returned_datetime:
                    if 'T' in returned_datetime:
                        parsed_datetime = datetime.fromisoformat(returned_datetime.replace('Z', ''))
                        
                        # Check if the date and time match what we intended
                        date_matches = (parsed_datetime.date() == lesson_datetime.date())
                        time_matches = (parsed_datetime.hour == lesson_datetime.hour and 
                                      parsed_datetime.minute == lesson_datetime.minute)
                        
                        if date_matches and time_matches:
                            successful_lessons += 1
                            self.created_lessons.append(lesson_id)
                            print(f"   ✅ Lesson created correctly: {parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            print(f"   ❌ Date/time mismatch - Expected: {lesson_datetime.strftime('%Y-%m-%d %H:%M')}, Got: {parsed_datetime.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        print(f"   ❌ Unexpected datetime format: {returned_datetime}")
                else:
                    print(f"   ❌ No start_datetime returned in response")
            else:
                print(f"   ❌ Failed to create lesson for {lesson_datetime.strftime('%Y-%m-%d')}")
        
        success = successful_lessons == len(test_dates)
        self.log_test("Lesson Creation Specific Dates", success, 
                     f"- {successful_lessons}/{len(test_dates)} lessons created on correct dates")
        return success

    def test_lesson_creation_various_times(self):
        """Test lesson creation with various times throughout the day"""
        print("\n🕐 Testing lesson creation with various times...")
        
        # Test different times throughout the day
        base_date = datetime.now() + timedelta(days=2)
        test_times = [
            base_date.replace(hour=9, minute=0),    # 9:00 AM
            base_date.replace(hour=12, minute=30),  # 12:30 PM
            base_date.replace(hour=15, minute=45),  # 3:45 PM
            base_date.replace(hour=18, minute=15),  # 6:15 PM
            base_date.replace(hour=20, minute=0),   # 8:00 PM
        ]
        
        successful_lessons = 0
        
        for i, test_time in enumerate(test_times):
            print(f"   🕐 Creating lesson for: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            lesson_data = {
                "student_id": self.created_student_id,
                "teacher_id": self.created_teacher_id,
                "start_datetime": test_time.strftime('%Y-%m-%dT%H:%M'),
                "duration_minutes": 60,
                "notes": f"Time test lesson - should be at {test_time.strftime('%H:%M')}"
            }
            
            success, response = self.make_request('POST', 'lessons', lesson_data, 200)
            
            if success:
                lesson_id = response.get('id')
                returned_datetime = response.get('start_datetime')
                
                if returned_datetime and 'T' in returned_datetime:
                    parsed_datetime = datetime.fromisoformat(returned_datetime.replace('Z', ''))
                    
                    # Verify exact time match
                    if (parsed_datetime.hour == test_time.hour and 
                        parsed_datetime.minute == test_time.minute):
                        successful_lessons += 1
                        self.created_lessons.append(lesson_id)
                        print(f"   ✅ Correct time: {parsed_datetime.strftime('%H:%M')}")
                    else:
                        print(f"   ❌ Time mismatch - Expected: {test_time.strftime('%H:%M')}, Got: {parsed_datetime.strftime('%H:%M')}")
                else:
                    print(f"   ❌ Invalid datetime format: {returned_datetime}")
            else:
                print(f"   ❌ Failed to create lesson for {test_time.strftime('%H:%M')}")
        
        success = successful_lessons == len(test_times)
        self.log_test("Lesson Creation Various Times", success, 
                     f"- {successful_lessons}/{len(test_times)} lessons created at correct times")
        return success

    def test_daily_calendar_date_consistency(self):
        """Test that lessons appear on the correct days in daily calendar"""
        print("\n📅 Testing daily calendar date consistency...")
        
        if not self.created_lessons:
            print("   ⚠️ No lessons created yet, skipping calendar test")
            return False
        
        # Test calendar for the dates we created lessons
        test_dates = [
            datetime.now() + timedelta(days=1),
            datetime.now() + timedelta(days=2),
            datetime.now() + timedelta(days=3),
        ]
        
        successful_calendar_checks = 0
        
        for test_date in test_dates:
            date_str = test_date.strftime('%Y-%m-%d')
            print(f"   📅 Checking calendar for: {date_str}")
            
            success, response = self.make_request('GET', f'calendar/daily/{date_str}', expected_status=200)
            
            if success:
                lessons = response.get('lessons', [])
                date_from_response = response.get('date', '')
                
                print(f"   📊 Found {len(lessons)} lessons on {date_from_response}")
                
                # Verify lessons on this date have correct dates
                date_consistent = True
                for lesson in lessons:
                    lesson_datetime = lesson.get('start_datetime', '')
                    if lesson_datetime and 'T' in lesson_datetime:
                        parsed_datetime = datetime.fromisoformat(lesson_datetime.replace('Z', ''))
                        lesson_date = parsed_datetime.date()
                        expected_date = test_date.date()
                        
                        if lesson_date != expected_date:
                            print(f"   ❌ Lesson date mismatch - Expected: {expected_date}, Got: {lesson_date}")
                            date_consistent = False
                        else:
                            print(f"   ✅ Lesson correctly on {lesson_date}")
                
                if date_consistent:
                    successful_calendar_checks += 1
            else:
                print(f"   ❌ Failed to get calendar for {date_str}")
        
        success = successful_calendar_checks > 0
        self.log_test("Daily Calendar Date Consistency", success, 
                     f"- {successful_calendar_checks}/{len(test_dates)} calendar dates consistent")
        return success

    def test_timezone_boundary_scenarios(self):
        """Test lesson creation across potential timezone boundaries"""
        print("\n🌍 Testing timezone boundary scenarios...")
        
        # Test edge cases that might cause timezone issues
        base_date = datetime.now() + timedelta(days=5)
        
        boundary_times = [
            base_date.replace(hour=0, minute=0),    # Midnight
            base_date.replace(hour=23, minute=59),  # Just before midnight
            base_date.replace(hour=12, minute=0),   # Noon
        ]
        
        successful_boundary_tests = 0
        
        for i, boundary_time in enumerate(boundary_times):
            print(f"   🕐 Testing boundary time: {boundary_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            lesson_data = {
                "student_id": self.created_student_id,
                "teacher_id": self.created_teacher_id,
                "start_datetime": boundary_time.strftime('%Y-%m-%dT%H:%M'),
                "duration_minutes": 60,
                "notes": f"Boundary test - {boundary_time.strftime('%H:%M')}"
            }
            
            success, response = self.make_request('POST', 'lessons', lesson_data, 200)
            
            if success:
                lesson_id = response.get('id')
                returned_datetime = response.get('start_datetime')
                
                if returned_datetime and 'T' in returned_datetime:
                    parsed_datetime = datetime.fromisoformat(returned_datetime.replace('Z', ''))
                    
                    # Check that the date hasn't shifted due to timezone conversion
                    date_matches = parsed_datetime.date() == boundary_time.date()
                    time_matches = (parsed_datetime.hour == boundary_time.hour and 
                                  parsed_datetime.minute == boundary_time.minute)
                    
                    if date_matches and time_matches:
                        successful_boundary_tests += 1
                        self.created_lessons.append(lesson_id)
                        print(f"   ✅ Boundary time preserved: {parsed_datetime.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        print(f"   ❌ Boundary time shifted - Expected: {boundary_time.strftime('%Y-%m-%d %H:%M')}, Got: {parsed_datetime.strftime('%Y-%m-%d %H:%M')}")
                else:
                    print(f"   ❌ Invalid datetime format: {returned_datetime}")
            else:
                print(f"   ❌ Failed to create boundary lesson")
        
        success = successful_boundary_tests == len(boundary_times)
        self.log_test("Timezone Boundary Scenarios", success, 
                     f"- {successful_boundary_tests}/{len(boundary_times)} boundary times preserved")
        return success

    def test_lesson_update_date_consistency(self):
        """Test that updating lesson times maintains date consistency"""
        print("\n✏️ Testing lesson update date consistency...")
        
        if not self.created_lessons:
            print("   ⚠️ No lessons available for update testing")
            return False
        
        # Use the first created lesson for update testing
        lesson_id = self.created_lessons[0]
        
        # New time for update
        new_datetime = datetime.now() + timedelta(days=6)
        new_datetime = new_datetime.replace(hour=16, minute=30, second=0, microsecond=0)
        
        print(f"   ✏️ Updating lesson to: {new_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        update_data = {
            "start_datetime": new_datetime.strftime('%Y-%m-%dT%H:%M'),
            "duration_minutes": 90,
            "notes": "Updated lesson - date consistency test"
        }
        
        success, response = self.make_request('PUT', f'lessons/{lesson_id}', update_data, 200)
        
        if success:
            returned_datetime = response.get('start_datetime')
            
            if returned_datetime and 'T' in returned_datetime:
                parsed_datetime = datetime.fromisoformat(returned_datetime.replace('Z', ''))
                
                date_matches = parsed_datetime.date() == new_datetime.date()
                time_matches = (parsed_datetime.hour == new_datetime.hour and 
                              parsed_datetime.minute == new_datetime.minute)
                
                if date_matches and time_matches:
                    print(f"   ✅ Update preserved date/time: {parsed_datetime.strftime('%Y-%m-%d %H:%M')}")
                    success = True
                else:
                    print(f"   ❌ Update changed date/time - Expected: {new_datetime.strftime('%Y-%m-%d %H:%M')}, Got: {parsed_datetime.strftime('%Y-%m-%d %H:%M')}")
                    success = False
            else:
                print(f"   ❌ Invalid datetime format after update: {returned_datetime}")
                success = False
        else:
            print("   ❌ Failed to update lesson")
            success = False
        
        self.log_test("Lesson Update Date Consistency", success, 
                     f"- Lesson update preserved intended date/time")
        return success

    def test_recurring_lesson_date_fix(self):
        """Test the specific recurring lesson timezone fix mentioned in the review"""
        print("\n🔄 Testing recurring lesson date handling fix...")
        
        # Test the specific scenario mentioned in the review request
        test_datetime = datetime.now() + timedelta(days=7)
        test_datetime = test_datetime.replace(hour=14, minute=0, second=0, microsecond=0)  # 2:00 PM
        
        print(f"   🕐 Creating recurring lessons starting: {test_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": test_datetime.strftime('%Y-%m-%dT%H:%M'),  # Local time format (no UTC conversion)
            "duration_minutes": 60,
            "recurrence_pattern": "weekly",
            "max_occurrences": 3,
            "notes": "Recurring lesson timezone fix test - should be at 2:00 PM exactly"
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        if not success:
            print("   ❌ Failed to create recurring lesson series")
            self.log_test("Recurring Lesson Date Fix", False, "- Could not create recurring series")
            return False
        
        series_id = response.get('series_id')
        lessons_created = response.get('lessons_created', 0)
        
        print(f"   📅 Created {lessons_created} recurring lessons")
        
        # Verify the generated lessons have correct times (should be 14:00, not 18:00)
        success, lessons_response = self.make_request('GET', 'lessons', expected_status=200)
        
        if not success:
            print("   ❌ Failed to retrieve lessons")
            self.log_test("Recurring Lesson Date Fix", False, "- Could not retrieve lessons")
            return False
        
        # Find lessons from our recurring series
        recurring_lessons = [lesson for lesson in lessons_response 
                           if lesson.get('recurring_series_id') == series_id]
        
        print(f"   🔍 Found {len(recurring_lessons)} lessons from recurring series")
        
        # Verify each lesson has the correct time (14:00, not offset by timezone)
        timezone_fix_working = True
        correct_time_count = 0
        
        for i, lesson in enumerate(recurring_lessons):
            start_datetime_str = lesson.get('start_datetime')
            if start_datetime_str and 'T' in start_datetime_str:
                lesson_datetime = datetime.fromisoformat(start_datetime_str.replace('Z', ''))
                lesson_hour = lesson_datetime.hour
                
                print(f"   📍 Lesson {i+1}: {lesson_datetime.strftime('%Y-%m-%d %H:%M:%S')} (Hour: {lesson_hour})")
                
                # The fix should ensure lessons are at 14:00 (2:00 PM), not 18:00 (6:00 PM)
                if lesson_hour == 14:
                    correct_time_count += 1
                    print(f"   ✅ Correct time: {lesson_hour}:00 (2:00 PM)")
                else:
                    print(f"   ❌ TIMEZONE ISSUE: Expected hour 14 (2:00 PM), got hour {lesson_hour}")
                    timezone_fix_working = False
            else:
                print(f"   ❌ Invalid datetime format in lesson {i+1}: {start_datetime_str}")
                timezone_fix_working = False
        
        # Clean up - cancel the recurring series
        if series_id:
            self.make_request('DELETE', f'recurring-lessons/{series_id}', expected_status=200)
        
        success = timezone_fix_working and correct_time_count == lessons_created
        
        self.log_test("Recurring Lesson Date Fix", success, 
                     f"- {correct_time_count}/{lessons_created} lessons at correct time (14:00)")
        return success

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created lessons
        for lesson_id in self.created_lessons:
            self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=200)
        
        # Delete test student and teacher
        if self.created_student_id:
            self.make_request('DELETE', f'students/{self.created_student_id}', expected_status=200)
        
        if self.created_teacher_id:
            self.make_request('DELETE', f'teachers/{self.created_teacher_id}', expected_status=200)
        
        print("✅ Cleanup completed")

    def run_all_tests(self):
        """Run all lesson date handling tests"""
        print("🚀 Starting Lesson Date Handling Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data, aborting tests")
            return
        
        # Run all tests
        tests = [
            self.test_lesson_creation_specific_dates,
            self.test_lesson_creation_various_times,
            self.test_daily_calendar_date_consistency,
            self.test_timezone_boundary_scenarios,
            self.test_lesson_update_date_consistency,
            self.test_recurring_lesson_date_fix,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
                self.tests_run += 1
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 LESSON DATE HANDLING TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL LESSON DATE HANDLING TESTS PASSED!")
            print("✅ Lessons are being created on the correct days without timezone issues")
        else:
            print("⚠️ Some tests failed - date handling may have issues")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = LessonDateHandlingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)