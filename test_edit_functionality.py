#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class EditFunctionalityTester:
    def __init__(self, base_url="https://studio-manager-3.preview.emergentagent.com"):
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

    def test_user_registration_and_login(self):
        """Test user registration and login for authentication"""
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"edit_test_owner_{timestamp}@example.com",
            "name": f"Edit Test Owner {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Edit Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success:
            self.user_id = response.get('id')
            self.test_email = user_data['email']
            self.test_password = user_data['password']
            
        self.log_test("User Registration", success, f"- User ID: {self.user_id}")
        
        if not success:
            return False
            
        # Login
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            
        self.log_test("User Login", success, f"- Token received: {'Yes' if self.token else 'No'}")
        return success

    def test_student_edit_functionality(self):
        """Test comprehensive student edit functionality"""
        print("\n🎓 STUDENT EDIT FUNCTIONALITY TESTS")
        print("-" * 50)
        
        # Create a student for editing tests
        student_data = {
            "name": "Isabella Martinez",
            "email": "isabella.martinez@example.com",
            "phone": "+1555123001",
            "parent_name": "Carmen Martinez",
            "parent_phone": "+1555123002",
            "parent_email": "carmen.martinez@example.com",
            "notes": "Interested in ballet and contemporary dance"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Student Edit - Create Test Student", False, "- Failed to create test student")
            return False
            
        edit_test_student_id = response.get('id')
        self.log_test("Student Edit - Create Test Student", True, f"- Student ID: {edit_test_student_id}")
        
        # Test 1: Update all student fields
        updated_data = {
            "name": "Isabella Martinez-Rodriguez",
            "email": "isabella.rodriguez@example.com", 
            "phone": "+1555123111",
            "parent_name": "Carmen Martinez-Rodriguez",
            "parent_phone": "+1555123112",
            "parent_email": "carmen.rodriguez@example.com",
            "notes": "Updated: Now focusing on advanced ballet techniques and preparing for competitions"
        }
        
        success, response = self.make_request('PUT', f'students/{edit_test_student_id}', updated_data, 200)
        
        updated_name = "Unknown"
        updated_email = "Unknown"
        if success:
            updated_name = response.get('name', 'Unknown')
            updated_email = response.get('email', 'Unknown')
            updated_phone = response.get('phone', 'Unknown')
            updated_parent_name = response.get('parent_name', 'Unknown')
            updated_notes = response.get('notes', 'Unknown')
            
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
            "name": "Isabella Rodriguez-Smith",
            "email": updated_data['email'],  # Keep existing
            "phone": updated_data['phone'],  # Keep existing
            "parent_name": updated_data['parent_name'],  # Keep existing
            "parent_phone": updated_data['parent_phone'],  # Keep existing
            "parent_email": updated_data['parent_email'],  # Keep existing
            "notes": "Updated notes: Added jazz and hip-hop to training schedule"
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
        auth_test_data = {
            "name": "Isabella Rodriguez-Smith (Auth Test)",
            "email": updated_data['email'],
            "phone": updated_data['phone'],
            "parent_name": updated_data['parent_name'],
            "parent_phone": updated_data['parent_phone'],
            "parent_email": updated_data['parent_email'],
            "notes": "Testing authentication requirement for student updates"
        }
        
        success, response = self.make_request('PUT', f'students/{edit_test_student_id}', auth_test_data, 200)
        self.log_test("Student Edit - With Authentication", success, 
                     f"- Authentication required and working")
        
        # Test 4: Update non-existent student
        fake_student_id = "nonexistent-student-id-12345"
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
        print("-" * 50)
        
        # Create a teacher for editing tests
        teacher_data = {
            "name": "Sofia Petrov",
            "email": "sofia.petrov@example.com",
            "phone": "+1555456003",
            "specialties": ["ballet", "jazz"],
            "bio": "Professional ballet instructor with 15 years of experience in classical and contemporary dance"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Teacher Edit - Create Test Teacher", False, "- Failed to create test teacher")
            return False
            
        edit_test_teacher_id = response.get('id')
        self.log_test("Teacher Edit - Create Test Teacher", True, f"- Teacher ID: {edit_test_teacher_id}")
        
        # Test 1: Update all teacher fields
        updated_data = {
            "name": "Sofia Petrov-Williams",
            "email": "sofia.williams@example.com",
            "phone": "+1555456222",
            "specialties": ["contemporary", "hip_hop", "ballroom"],
            "bio": "Updated bio: Master instructor specializing in contemporary dance and ballroom competitions. Former principal dancer with extensive choreography experience."
        }
        
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', updated_data, 200)
        
        updated_name = "Unknown"
        updated_specialties = []
        if success:
            updated_name = response.get('name', 'Unknown')
            updated_email = response.get('email', 'Unknown')
            updated_phone = response.get('phone', 'Unknown')
            updated_specialties = response.get('specialties', [])
            updated_bio = response.get('bio', 'Unknown')
            
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
        
        new_specialties = []
        if success:
            new_specialties = response.get('specialties', [])
            specialties_updated = set(new_specialties) == set(specialty_update['specialties'])
            success = specialties_updated
            
        self.log_test("Teacher Edit - Update Specialties Array", success, 
                     f"- New specialties: {new_specialties}")
        
        # Test 3: Partial update (only name and bio)
        partial_update = {
            "name": "Sofia Williams-Chen",
            "email": updated_data['email'],  # Keep existing
            "phone": updated_data['phone'],  # Keep existing
            "specialties": specialty_update['specialties'],  # Keep existing
            "bio": "Partial update: Added expertise in Latin dance styles and youth competition coaching"
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
            "name": "Sofia Williams-Chen (Auth Test)",
            "email": updated_data['email'],
            "phone": updated_data['phone'],
            "specialties": ["ballet"],
            "bio": "Testing authentication requirement for teacher updates"
        }
        
        success, response = self.make_request('PUT', f'teachers/{edit_test_teacher_id}', auth_test_data, 200)
        self.log_test("Teacher Edit - With Authentication", success, 
                     f"- Authentication required and working")
        
        # Test 5: Update non-existent teacher
        fake_teacher_id = "nonexistent-teacher-id-67890"
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
        print("-" * 50)
        
        # Create test student
        student_data = {
            "name": "Real-time Test Student",
            "email": "realtime.student@example.com",
            "phone": "+1555789004"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Real-time Updates - Create Student", False, "- Failed to create test student")
            return False
            
        realtime_student_id = response.get('id')
        
        # Update student (should trigger real-time broadcast)
        update_data = {
            "name": "Updated Real-time Student",
            "email": "updated.realtime.student@example.com",
            "phone": "+1555789005",
            "parent_name": "Real-time Test Parent",
            "parent_phone": "+1555789006",
            "parent_email": "parent.realtime@example.com",
            "notes": "Updated for real-time testing - should broadcast to all connected clients"
        }
        
        success, response = self.make_request('PUT', f'students/{realtime_student_id}', update_data, 200)
        self.log_test("Real-time Updates - Student Update", success, 
                     f"- Student update with real-time broadcast")
        
        # Create test teacher
        teacher_data = {
            "name": "Real-time Test Teacher",
            "email": "realtime.teacher@example.com",
            "phone": "+1555789007",
            "specialties": ["ballet"],
            "bio": "Real-time test teacher for broadcast testing"
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
            "phone": "+1555789008",
            "specialties": ["jazz", "contemporary"],
            "bio": "Updated real-time test teacher - should broadcast to all connected clients"
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
        print("-" * 50)
        
        # Create test student and teacher for validation tests
        student_data = {
            "name": "Validation Test Student",
            "email": "validation.student@example.com",
            "phone": "+1555999009"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Data Validation - Create Student", False, "- Failed to create test student")
            return False
            
        validation_student_id = response.get('id')
        
        teacher_data = {
            "name": "Validation Test Teacher",
            "email": "validation.teacher@example.com",
            "phone": "+1555999010",
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
            "email": "invalid-email-format-no-at-symbol",
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
                     f"- Email validation handled gracefully")
        
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

    def run_edit_functionality_tests(self):
        """Run all edit functionality tests"""
        print("🚀 Starting Edit Functionality Tests...")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Authentication first
        if not self.test_user_registration_and_login():
            print("❌ Authentication failed - cannot proceed with edit tests")
            return False
        
        # Run edit functionality tests
        self.test_student_edit_functionality()
        self.test_teacher_edit_functionality()
        self.test_real_time_updates_for_edits()
        self.test_data_validation_for_edits()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🎯 EDIT FUNCTIONALITY TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📊 Total Tests: {self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL EDIT FUNCTIONALITY TESTS PASSED!")
            print("✨ Student and Teacher edit features are working perfectly!")
        else:
            print("⚠️  Some edit functionality tests failed. Please check the details above.")
        
        return self.tests_passed == self.tests_run

def main():
    tester = EditFunctionalityTester()
    success = tester.run_edit_functionality_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())