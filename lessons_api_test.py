#!/usr/bin/env python3
"""
Focused test for Lessons API endpoint to diagnose weekly calendar past lessons issue.
Testing objectives:
1. Test GET /api/lessons endpoint
2. Verify it returns all lessons including past lessons
3. Check date format and structure of returned lessons
4. Verify lesson data structure matches what weekly calendar expects
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class LessonsAPITester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
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

    def test_admin_login(self):
        """Test login with admin@test.com / admin123 credentials"""
        print("\n🔐 Testing Admin Authentication...")
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            user_info = response.get('user', {})
            print(f"   👤 Admin user: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            
        self.log_test("Admin Login", success, f"- Admin token received: {'Yes' if self.token else 'No'}")
        return success

    def test_lessons_api_basic(self):
        """Test basic GET /api/lessons endpoint functionality"""
        print("\n📚 Testing Basic Lessons API...")
        
        success, response = self.make_request('GET', 'lessons', expected_status=200)
        
        if success:
            lessons = response if isinstance(response, list) else []
            print(f"   📊 Total lessons returned: {len(lessons)}")
            
            if lessons:
                print(f"   📝 Sample lesson structure:")
                sample_lesson = lessons[0]
                for key, value in sample_lesson.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"      {key}: {value}")
        
        self.log_test("Basic Lessons API", success, f"- Lessons count: {len(lessons) if success else 'N/A'}")
        return success, response if success else []

    def analyze_lesson_dates(self, lessons: List[Dict]):
        """Analyze lesson dates to categorize past, present, and future lessons"""
        print("\n📅 Analyzing Lesson Date Ranges...")
        
        if not lessons:
            self.log_test("Date Range Analysis", False, "- No lessons to analyze")
            return False
        
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        past_lessons = []
        today_lessons = []
        future_lessons = []
        invalid_dates = []
        
        for lesson in lessons:
            try:
                # Handle different datetime formats
                start_datetime_str = lesson.get('start_datetime', '')
                if not start_datetime_str:
                    invalid_dates.append(lesson.get('id', 'unknown'))
                    continue
                
                # Parse datetime
                if isinstance(start_datetime_str, str):
                    if start_datetime_str.endswith('Z'):
                        lesson_datetime = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
                    else:
                        lesson_datetime = datetime.fromisoformat(start_datetime_str)
                else:
                    lesson_datetime = start_datetime_str
                
                # Remove timezone info for comparison
                lesson_date = lesson_datetime.replace(tzinfo=None)
                
                if lesson_date.date() < today.date():
                    past_lessons.append(lesson)
                elif lesson_date.date() == today.date():
                    today_lessons.append(lesson)
                else:
                    future_lessons.append(lesson)
                    
            except Exception as e:
                print(f"   ⚠️  Error parsing date for lesson {lesson.get('id', 'unknown')}: {e}")
                invalid_dates.append(lesson.get('id', 'unknown'))
        
        print(f"   📊 Date Range Analysis:")
        print(f"      📅 Past lessons: {len(past_lessons)}")
        print(f"      📅 Today's lessons: {len(today_lessons)}")
        print(f"      📅 Future lessons: {len(future_lessons)}")
        print(f"      ⚠️  Invalid dates: {len(invalid_dates)}")
        
        # Show sample past lessons
        if past_lessons:
            print(f"\n   🔍 Sample Past Lessons (showing first 3):")
            for i, lesson in enumerate(past_lessons[:3]):
                student_name = lesson.get('student_name', 'Unknown')
                teacher_names = lesson.get('teacher_names', [])
                start_datetime = lesson.get('start_datetime', 'Unknown')
                lesson_id = lesson.get('id', 'Unknown')
                status = lesson.get('status', lesson.get('is_cancelled', False))
                
                print(f"      {i+1}. ID: {lesson_id}")
                print(f"         Student: {student_name}")
                print(f"         Teachers: {', '.join(teacher_names) if teacher_names else 'Unknown'}")
                print(f"         Date/Time: {start_datetime}")
                print(f"         Status: {status}")
                print()
        
        success = len(past_lessons) > 0
        self.log_test("Past Lessons Found", success, f"- Found {len(past_lessons)} past lessons")
        
        return {
            'past_lessons': past_lessons,
            'today_lessons': today_lessons,
            'future_lessons': future_lessons,
            'invalid_dates': invalid_dates,
            'total_lessons': len(lessons)
        }

    def verify_lesson_data_structure(self, lessons: List[Dict]):
        """Verify lesson data structure matches what weekly calendar expects"""
        print("\n🔍 Verifying Lesson Data Structure...")
        
        if not lessons:
            self.log_test("Data Structure Verification", False, "- No lessons to verify")
            return False
        
        required_fields = [
            'id', 'student_id', 'student_name', 'teacher_ids', 'teacher_names',
            'start_datetime', 'end_datetime', 'booking_type', 'status'
        ]
        
        optional_fields = [
            'notes', 'is_attended', 'enrollment_id', 'recurring_series_id',
            'is_cancelled', 'cancellation_reason', 'cancelled_at', 'cancelled_by'
        ]
        
        structure_issues = []
        valid_lessons = 0
        
        for i, lesson in enumerate(lessons[:10]):  # Check first 10 lessons
            lesson_issues = []
            
            # Check required fields
            for field in required_fields:
                if field not in lesson:
                    lesson_issues.append(f"Missing required field: {field}")
                elif lesson[field] is None:
                    lesson_issues.append(f"Required field is null: {field}")
            
            # Check data types
            if 'teacher_ids' in lesson and not isinstance(lesson['teacher_ids'], list):
                lesson_issues.append("teacher_ids should be a list")
            
            if 'teacher_names' in lesson and not isinstance(lesson['teacher_names'], list):
                lesson_issues.append("teacher_names should be a list")
            
            # Check datetime format
            try:
                start_dt = lesson.get('start_datetime')
                if start_dt:
                    if isinstance(start_dt, str):
                        datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
            except Exception as e:
                lesson_issues.append(f"Invalid start_datetime format: {e}")
            
            if lesson_issues:
                structure_issues.append({
                    'lesson_id': lesson.get('id', f'lesson_{i}'),
                    'issues': lesson_issues
                })
            else:
                valid_lessons += 1
        
        print(f"   📊 Structure Analysis (first 10 lessons):")
        print(f"      ✅ Valid lessons: {valid_lessons}")
        print(f"      ❌ Lessons with issues: {len(structure_issues)}")
        
        if structure_issues:
            print(f"\n   ⚠️  Structure Issues Found:")
            for issue in structure_issues[:3]:  # Show first 3 issues
                print(f"      Lesson {issue['lesson_id']}:")
                for problem in issue['issues']:
                    print(f"        - {problem}")
        
        success = len(structure_issues) == 0
        self.log_test("Data Structure Verification", success, 
                     f"- {valid_lessons} valid, {len(structure_issues)} with issues")
        
        return success

    def test_date_filtering(self, lessons: List[Dict]):
        """Test if lessons can be filtered by date ranges"""
        print("\n🗓️  Testing Date Filtering Capabilities...")
        
        if not lessons:
            self.log_test("Date Filtering Test", False, "- No lessons to filter")
            return False
        
        # Test filtering lessons for a specific week
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())  # Monday of current week
        week_end = week_start + timedelta(days=6)  # Sunday of current week
        
        current_week_lessons = []
        past_week_lessons = []
        
        for lesson in lessons:
            try:
                start_datetime_str = lesson.get('start_datetime', '')
                if start_datetime_str:
                    if isinstance(start_datetime_str, str):
                        if start_datetime_str.endswith('Z'):
                            lesson_datetime = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
                        else:
                            lesson_datetime = datetime.fromisoformat(start_datetime_str)
                    else:
                        lesson_datetime = start_datetime_str
                    
                    lesson_date = lesson_datetime.replace(tzinfo=None)
                    
                    if week_start <= lesson_date <= week_end:
                        current_week_lessons.append(lesson)
                    elif lesson_date < week_start:
                        past_week_lessons.append(lesson)
                        
            except Exception as e:
                print(f"   ⚠️  Error filtering lesson {lesson.get('id', 'unknown')}: {e}")
        
        print(f"   📊 Filtering Results:")
        print(f"      📅 Current week lessons: {len(current_week_lessons)}")
        print(f"      📅 Past week lessons: {len(past_week_lessons)}")
        print(f"      📅 Week range: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
        
        # Test if past lessons are accessible for weekly calendar
        success = len(past_week_lessons) > 0 or len(current_week_lessons) > 0
        self.log_test("Date Filtering Test", success, 
                     f"- Found {len(past_week_lessons)} past + {len(current_week_lessons)} current week lessons")
        
        return success

    def test_lesson_status_filtering(self, lessons: List[Dict]):
        """Test lesson status filtering to see if cancelled/completed lessons are included"""
        print("\n🏷️  Testing Lesson Status Filtering...")
        
        if not lessons:
            self.log_test("Status Filtering Test", False, "- No lessons to analyze")
            return False
        
        status_counts = {}
        cancelled_lessons = []
        active_lessons = []
        attended_lessons = []
        
        for lesson in lessons:
            # Check new status field
            status = lesson.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts[status] = 1
            
            # Check legacy fields
            is_cancelled = lesson.get('is_cancelled', False)
            is_attended = lesson.get('is_attended', False)
            
            if is_cancelled or status == 'cancelled':
                cancelled_lessons.append(lesson)
            elif is_attended or status == 'completed':
                attended_lessons.append(lesson)
            else:
                active_lessons.append(lesson)
        
        print(f"   📊 Status Analysis:")
        print(f"      📈 Status distribution:")
        for status, count in status_counts.items():
            print(f"        {status}: {count}")
        print(f"      ❌ Cancelled lessons: {len(cancelled_lessons)}")
        print(f"      ✅ Attended lessons: {len(attended_lessons)}")
        print(f"      🟢 Active lessons: {len(active_lessons)}")
        
        # Check if past lessons might be filtered out due to status
        past_lessons_by_status = {'active': 0, 'cancelled': 0, 'attended': 0}
        now = datetime.utcnow()
        
        for lesson in lessons:
            try:
                start_datetime_str = lesson.get('start_datetime', '')
                if start_datetime_str:
                    if isinstance(start_datetime_str, str):
                        lesson_datetime = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
                    else:
                        lesson_datetime = start_datetime_str
                    
                    if lesson_datetime.replace(tzinfo=None) < now:
                        if lesson.get('is_cancelled', False) or lesson.get('status') == 'cancelled':
                            past_lessons_by_status['cancelled'] += 1
                        elif lesson.get('is_attended', False) or lesson.get('status') == 'completed':
                            past_lessons_by_status['attended'] += 1
                        else:
                            past_lessons_by_status['active'] += 1
            except:
                continue
        
        print(f"   📅 Past Lessons by Status:")
        for status, count in past_lessons_by_status.items():
            print(f"      {status}: {count}")
        
        success = True  # Status filtering test always passes, it's informational
        self.log_test("Status Filtering Analysis", success, 
                     f"- {len(cancelled_lessons)} cancelled, {len(attended_lessons)} attended, {len(active_lessons)} active")
        
        return success

    def run_comprehensive_lessons_test(self):
        """Run comprehensive lessons API testing"""
        print("🎯 COMPREHENSIVE LESSONS API TESTING FOR WEEKLY CALENDAR DIAGNOSIS")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.test_admin_login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Test basic lessons API
        success, lessons = self.test_lessons_api_basic()
        if not success:
            print("❌ Cannot proceed without basic API access")
            return False
        
        # Step 3: Analyze date ranges
        date_analysis = self.analyze_lesson_dates(lessons)
        
        # Step 4: Verify data structure
        self.verify_lesson_data_structure(lessons)
        
        # Step 5: Test date filtering
        self.test_date_filtering(lessons)
        
        # Step 6: Test status filtering
        self.test_lesson_status_filtering(lessons)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TESTING SUMMARY")
        print("=" * 80)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if isinstance(date_analysis, dict):
            print(f"\n🔍 KEY FINDINGS:")
            print(f"   📚 Total lessons in database: {date_analysis['total_lessons']}")
            print(f"   📅 Past lessons available: {len(date_analysis['past_lessons'])}")
            print(f"   📅 Today's lessons: {len(date_analysis['today_lessons'])}")
            print(f"   📅 Future lessons: {len(date_analysis['future_lessons'])}")
            
            if len(date_analysis['past_lessons']) == 0:
                print(f"\n⚠️  POTENTIAL ISSUE: No past lessons found!")
                print(f"   This could explain why past lessons don't show in weekly calendar.")
                print(f"   Recommendation: Check if lessons are being created with past dates.")
            else:
                print(f"\n✅ Past lessons are available in the API response.")
                print(f"   The issue might be in frontend filtering or weekly calendar logic.")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = LessonsAPITester()
    success = tester.run_comprehensive_lessons_test()
    
    if success:
        print("\n🎉 All tests passed! Lessons API is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    exit(0 if success else 1)