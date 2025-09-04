#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class ComprehensiveDanceProgramTester:
    def __init__(self, base_url="https://rhythm-scheduler-1.preview.emergentagent.com"):
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
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"comprehensive_test_{timestamp}@example.com",
            "name": f"Comprehensive Tester {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Comprehensive Test Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success:
            login_data = {
                "email": user_data['email'],
                "password": user_data['password']
            }
            
            success, login_response = self.make_request('POST', 'auth/login', login_data, 200)
            
            if success:
                self.token = login_response.get('access_token')
                
        self.log_test("Authentication Setup", success, f"- Token: {'Yes' if self.token else 'No'}")
        return success

    def test_dashboard_stats_with_programs(self):
        """Test dashboard stats include enrollment data from new program system"""
        success, response = self.make_request('GET', 'dashboard/stats', expected_status=200)
        
        if success:
            required_fields = ['total_classes', 'total_teachers', 'total_students', 'active_enrollments', 
                             'classes_today', 'lessons_today', 'lessons_attended_today', 'estimated_monthly_revenue']
            has_all_fields = all(field in response for field in required_fields)
            
            # Check that we have active enrollments (should include both old and new format)
            active_enrollments = response.get('active_enrollments', 0)
            estimated_revenue = response.get('estimated_monthly_revenue', 0)
            
            success = has_all_fields and active_enrollments > 0 and estimated_revenue > 0
            
        self.log_test("Dashboard Stats with Programs", success, 
                     f"- Active Enrollments: {active_enrollments}, Revenue: ${estimated_revenue}")
        return success

    def test_program_level_distribution(self):
        """Test that programs are properly distributed across levels"""
        success, response = self.make_request('GET', 'programs', expected_status=200)
        
        if success:
            level_counts = {}
            for program in response:
                level = program.get('level', 'Unknown')
                level_counts[level] = level_counts.get(level, 0) + 1
            
            # Expected distribution
            expected_levels = {
                'Beginner': 1,  # Beginner Program
                'Social': 1,    # Social Foundation
                'Bronze': 3,    # Newcomers, Beginner, Intermediate, Full Bronze
                'Silver': 3,    # Beginner, Intermediate, Full Silver
                'Gold': 3       # Beginner, Intermediate, Full Gold
            }
            
            success = all(level_counts.get(level, 0) >= count for level, count in expected_levels.items())
            
        self.log_test("Program Level Distribution", success, f"- Level counts: {level_counts}")
        return success

    def test_enrollment_migration_compatibility(self):
        """Test that old package-based enrollments work with new system"""
        success, response = self.make_request('GET', 'enrollments', expected_status=200)
        
        if success:
            # Look for legacy enrollments (should have "Legacy Package:" in program_name)
            legacy_enrollments = [e for e in response if e.get('program_name', '').startswith('Legacy Package:')]
            new_enrollments = [e for e in response if not e.get('program_name', '').startswith('Legacy Package:')]
            
            # All enrollments should have required fields
            all_have_required_fields = all(
                'program_name' in e and 'total_lessons' in e and 'remaining_lessons' in e
                for e in response
            )
            
            success = all_have_required_fields and len(response) > 0
            
        self.log_test("Enrollment Migration Compatibility", success, 
                     f"- Total: {len(response)}, Legacy: {len(legacy_enrollments)}, New: {len(new_enrollments)}")
        return success

    def test_full_enrollment_workflow(self):
        """Test complete enrollment workflow with new program system"""
        # Create student
        student_data = {
            "name": "Workflow Test Student",
            "email": "workflow.test@example.com",
            "phone": "+1555999888"
        }
        
        success, student_response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Full Enrollment Workflow", False, "- Failed to create student")
            return False
            
        student_id = student_response.get('id')
        
        # Create teacher
        teacher_data = {
            "name": "Workflow Test Teacher",
            "email": "workflow.teacher@example.com",
            "specialties": ["ballet", "contemporary"]
        }
        
        success, teacher_response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Full Enrollment Workflow", False, "- Failed to create teacher")
            return False
            
        teacher_id = teacher_response.get('id')
        
        # Create enrollment with Full Silver program
        enrollment_data = {
            "student_id": student_id,
            "program_name": "Full Silver",
            "total_lessons": 20,
            "total_paid": 1000.0
        }
        
        success, enrollment_response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if not success:
            self.log_test("Full Enrollment Workflow", False, "- Failed to create enrollment")
            return False
            
        enrollment_id = enrollment_response.get('id')
        initial_lessons = enrollment_response.get('remaining_lessons', 0)
        
        # Create lesson linked to enrollment
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": student_id,
            "teacher_id": teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "notes": "Full Silver program lesson",
            "enrollment_id": enrollment_id
        }
        
        success, lesson_response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Full Enrollment Workflow", False, "- Failed to create lesson")
            return False
            
        lesson_id = lesson_response.get('id')
        
        # Mark lesson as attended
        success, attend_response = self.make_request('POST', f'lessons/{lesson_id}/attend', expected_status=200)
        if not success:
            self.log_test("Full Enrollment Workflow", False, "- Failed to mark lesson attended")
            return False
            
        # Verify lesson was deducted from enrollment
        success, final_enrollments = self.make_request('GET', f'students/{student_id}/enrollments', expected_status=200)
        if not success:
            self.log_test("Full Enrollment Workflow", False, "- Failed to get final enrollments")
            return False
            
        final_lessons = final_enrollments[0].get('remaining_lessons', 0) if final_enrollments else 0
        lessons_deducted = initial_lessons - final_lessons
        
        success = lessons_deducted == 1
        
        self.log_test("Full Enrollment Workflow", success, 
                     f"- Lessons: {initial_lessons} → {final_lessons} (deducted: {lessons_deducted})")
        return success

    def test_program_name_flexibility(self):
        """Test that system accepts various program names"""
        # Create test student
        student_data = {
            "name": "Flexibility Test Student",
            "email": "flexibility.test@example.com"
        }
        
        success, student_response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Program Name Flexibility", False, "- Failed to create student")
            return False
            
        student_id = student_response.get('id')
        
        # Test various program names
        test_programs = [
            "Custom Private Lessons",
            "Wedding Dance Preparation",
            "Competition Training",
            "Adult Beginner Special",
            "Kids Summer Camp"
        ]
        
        successful_enrollments = 0
        
        for program_name in test_programs:
            enrollment_data = {
                "student_id": student_id,
                "program_name": program_name,
                "total_lessons": 5,
                "total_paid": 250.0
            }
            
            success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
            if success:
                successful_enrollments += 1
                print(f"   ✅ Created enrollment for: {program_name}")
            else:
                print(f"   ❌ Failed to create enrollment for: {program_name}")
        
        success = successful_enrollments == len(test_programs)
        
        self.log_test("Program Name Flexibility", success, 
                     f"- {successful_enrollments}/{len(test_programs)} custom programs accepted")
        return success

    def run_comprehensive_tests(self):
        """Run comprehensive tests for the dance program system"""
        print("🎭 Starting Comprehensive Dance Program System Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Setup
        print("\n🔧 Setup:")
        if not self.setup_auth():
            print("❌ Authentication setup failed, aborting tests")
            return 1
        
        # Comprehensive tests
        print("\n📊 Dashboard Integration Tests:")
        self.test_dashboard_stats_with_programs()
        
        print("\n🎯 Program Structure Tests:")
        self.test_program_level_distribution()
        
        print("\n🔄 Migration Compatibility Tests:")
        self.test_enrollment_migration_compatibility()
        
        print("\n🔗 Full Workflow Tests:")
        self.test_full_enrollment_workflow()
        
        print("\n🎨 Flexibility Tests:")
        self.test_program_name_flexibility()
        
        # Final results
        print("\n" + "=" * 70)
        print(f"📊 Comprehensive Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All comprehensive tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = ComprehensiveDanceProgramTester()
    return tester.run_comprehensive_tests()

if __name__ == "__main__":
    sys.exit(main())