import requests
import json
from datetime import datetime, timedelta

def test_comprehensive_delete_functionality():
    """Comprehensive test of delete functionality with authentication"""
    base_url = 'https://40cca8f8-7cce-4162-b27d-7b2165da8a53.preview.emergentagent.com/api'
    
    print("🔐 Comprehensive Delete Functionality Test")
    print("=" * 50)
    
    # 1. Register and login
    timestamp = datetime.now().strftime("%H%M%S")
    user_data = {
        'email': f'comprehensive_test_{timestamp}@example.com',
        'name': f'Comprehensive Test User {timestamp}',
        'password': 'TestPassword123!',
        'role': 'owner',
        'studio_name': 'Comprehensive Test Studio'
    }
    
    response = requests.post(f'{base_url}/auth/register', json=user_data)
    print(f"✅ Registration: {response.status_code == 200}")
    
    login_data = {
        'email': user_data['email'],
        'password': user_data['password']
    }
    
    response = requests.post(f'{base_url}/auth/login', json=login_data)
    print(f"✅ Login: {response.status_code == 200}")
    
    if response.status_code != 200:
        print("❌ Authentication failed")
        return
        
    token = response.json().get('access_token')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # 2. Create test data
    teacher_data = {
        'name': 'Comprehensive Test Teacher',
        'email': 'comp.teacher@example.com',
        'phone': '+1555111222',
        'specialties': ['ballet', 'jazz'],
        'bio': 'Teacher for comprehensive testing'
    }
    
    response = requests.post(f'{base_url}/teachers', json=teacher_data, headers=headers)
    print(f"✅ Teacher Creation: {response.status_code == 200}")
    teacher_id = response.json().get('id') if response.status_code == 200 else None
    
    student_data = {
        'name': 'Comprehensive Test Student',
        'email': 'comp.student@example.com',
        'phone': '+1555333444',
        'parent_name': 'Test Parent',
        'parent_phone': '+1555333445',
        'parent_email': 'test.parent@example.com',
        'notes': 'Student for comprehensive testing'
    }
    
    response = requests.post(f'{base_url}/students', json=student_data, headers=headers)
    print(f"✅ Student Creation: {response.status_code == 200}")
    student_id = response.json().get('id') if response.status_code == 200 else None
    
    if not teacher_id or not student_id:
        print("❌ Failed to create test data")
        return
    
    # Create lesson
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    
    lesson_data = {
        'student_id': student_id,
        'teacher_id': teacher_id,
        'start_datetime': start_time.isoformat(),
        'duration_minutes': 60,
        'notes': 'Lesson for comprehensive testing'
    }
    
    response = requests.post(f'{base_url}/lessons', json=lesson_data, headers=headers)
    print(f"✅ Lesson Creation: {response.status_code == 200}")
    lesson_id = response.json().get('id') if response.status_code == 200 else None
    
    # 3. Test delete with valid authentication
    print("\n🔑 Testing Delete with Valid Authentication:")
    
    # Delete lesson
    if lesson_id:
        response = requests.delete(f'{base_url}/lessons/{lesson_id}', headers=headers)
        success = response.status_code == 200
        print(f"✅ Delete Lesson: {success}")
        if success:
            result = response.json()
            print(f"   Message: {result.get('message', 'No message')}")
    
    # Delete student
    if student_id:
        response = requests.delete(f'{base_url}/students/{student_id}', headers=headers)
        success = response.status_code == 200
        print(f"✅ Delete Student: {success}")
        if success:
            result = response.json()
            print(f"   Message: {result.get('message', 'No message')}")
            print(f"   Associated Lessons: {result.get('associated_lessons', 0)}")
            print(f"   Associated Enrollments: {result.get('associated_enrollments', 0)}")
    
    # Delete teacher
    if teacher_id:
        response = requests.delete(f'{base_url}/teachers/{teacher_id}', headers=headers)
        success = response.status_code == 200
        print(f"✅ Delete Teacher: {success}")
        if success:
            result = response.json()
            print(f"   Message: {result.get('message', 'No message')}")
            print(f"   Associated Lessons: {result.get('associated_lessons', 0)}")
            print(f"   Associated Classes: {result.get('associated_classes', 0)}")
    
    # 4. Test delete without authentication
    print("\n🚫 Testing Delete without Authentication:")
    
    # Create new teacher for no-auth test
    response = requests.post(f'{base_url}/teachers', json=teacher_data, headers=headers)
    if response.status_code == 200:
        no_auth_teacher_id = response.json().get('id')
        
        # Try to delete without auth
        response = requests.delete(f'{base_url}/teachers/{no_auth_teacher_id}')
        success = response.status_code in [401, 403]
        print(f"✅ Delete Teacher without Auth: {success} (Status: {response.status_code})")
        
        # Clean up
        requests.delete(f'{base_url}/teachers/{no_auth_teacher_id}', headers=headers)
    
    # 5. Test delete with invalid authentication
    print("\n🔐 Testing Delete with Invalid Authentication:")
    
    # Create new student for invalid-auth test
    response = requests.post(f'{base_url}/students', json=student_data, headers=headers)
    if response.status_code == 200:
        invalid_auth_student_id = response.json().get('id')
        
        # Try to delete with invalid token
        invalid_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer invalid_token_123'
        }
        
        response = requests.delete(f'{base_url}/students/{invalid_auth_student_id}', headers=invalid_headers)
        success = response.status_code == 401
        print(f"✅ Delete Student with Invalid Auth: {success} (Status: {response.status_code})")
        
        # Clean up
        requests.delete(f'{base_url}/students/{invalid_auth_student_id}', headers=headers)
    
    # 6. Test delete non-existent records
    print("\n🔍 Testing Delete Non-existent Records:")
    
    fake_ids = ['fake-teacher-id', 'fake-student-id', 'fake-lesson-id']
    endpoints = ['teachers', 'students', 'lessons']
    
    for endpoint, fake_id in zip(endpoints, fake_ids):
        response = requests.delete(f'{base_url}/{endpoint}/{fake_id}', headers=headers)
        success = response.status_code == 404
        print(f"✅ Delete Non-existent {endpoint[:-1].title()}: {success} (Status: {response.status_code})")
    
    print("\n🎉 Comprehensive Delete Functionality Test Complete!")

if __name__ == "__main__":
    test_comprehensive_delete_functionality()