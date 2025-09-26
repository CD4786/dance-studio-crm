#!/usr/bin/env python3
"""
User Management System Testing
Focus: Diagnose user deletion "User not found" error
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

class UserManagementTester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.admin_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.all_users = []
        self.test_user_ids = []

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
        
        if self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'

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

    def test_admin_authentication(self):
        """Test admin login with admin@test.com / admin123"""
        print("\n🔐 TESTING ADMIN AUTHENTICATION")
        
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.admin_token = response.get('access_token')
            user_info = response.get('user', {})
            self.admin_user_id = user_info.get('id')
            print(f"   👤 Admin user: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            print(f"   🆔 Admin ID: {self.admin_user_id}")
            print(f"   🔑 Token length: {len(self.admin_token) if self.admin_token else 0} chars")
            
        self.log_test("Admin Authentication", success, f"- Token: {'✓' if self.admin_token else '✗'}")
        return success

    def test_get_all_users(self):
        """Test GET /api/users endpoint to see all existing users"""
        print("\n👥 TESTING GET ALL USERS")
        
        if not self.admin_token:
            self.log_test("Get All Users", False, "- No admin token available")
            return False
            
        success, response = self.make_request('GET', 'users', expected_status=200)
        
        if success:
            self.all_users = response if isinstance(response, list) else []
            users_count = len(self.all_users)
            
            print(f"   📊 Total users found: {users_count}")
            
            # Display user details
            for i, user in enumerate(self.all_users[:10]):  # Show first 10 users
                user_id = user.get('id', 'No ID')
                name = user.get('name', 'No Name')
                email = user.get('email', 'No Email')
                role = user.get('role', 'No Role')
                is_active = user.get('is_active', False)
                
                print(f"   {i+1:2d}. ID: {user_id[:8]}... | {name} | {email} | {role} | {'Active' if is_active else 'Inactive'}")
                
            if users_count > 10:
                print(f"   ... and {users_count - 10} more users")
                
            # Find admin user
            admin_user = None
            for user in self.all_users:
                if user.get('email') == 'admin@test.com':
                    admin_user = user
                    break
                    
            if admin_user:
                print(f"   🎯 Admin user found: ID={admin_user.get('id')}, Role={admin_user.get('role')}")
            else:
                print(f"   ⚠️  Admin user not found in user list!")
                
        self.log_test("Get All Users", success, f"- Found {len(self.all_users)} users")
        return success

    def test_user_id_format_verification(self):
        """Test user ID format and structure"""
        print("\n🔍 TESTING USER ID FORMAT")
        
        if not self.all_users:
            self.log_test("User ID Format Verification", False, "- No users available")
            return False
            
        uuid_format_count = 0
        objectid_format_count = 0
        other_format_count = 0
        
        for user in self.all_users:
            user_id = user.get('id', '')
            
            # Check if it's UUID format (36 chars with dashes)
            if len(user_id) == 36 and user_id.count('-') == 4:
                uuid_format_count += 1
            # Check if it's ObjectId format (24 hex chars)
            elif len(user_id) == 24 and all(c in '0123456789abcdef' for c in user_id.lower()):
                objectid_format_count += 1
            else:
                other_format_count += 1
                print(f"   ⚠️  Unusual ID format: {user_id}")
                
        print(f"   📋 ID Format Analysis:")
        print(f"      UUID format: {uuid_format_count}")
        print(f"      ObjectId format: {objectid_format_count}")
        print(f"      Other format: {other_format_count}")
        
        # Most should be UUID format based on the backend code
        success = uuid_format_count > 0
        
        self.log_test("User ID Format Verification", success, 
                     f"- UUID: {uuid_format_count}, ObjectId: {objectid_format_count}, Other: {other_format_count}")
        return success

    def test_admin_user_verification(self):
        """Verify admin user exists and get correct ID"""
        print("\n🎯 TESTING ADMIN USER VERIFICATION")
        
        if not self.all_users:
            self.log_test("Admin User Verification", False, "- No users available")
            return False
            
        admin_user = None
        for user in self.all_users:
            if user.get('email') == 'admin@test.com':
                admin_user = user
                break
                
        if not admin_user:
            self.log_test("Admin User Verification", False, "- Admin user not found")
            return False
            
        # Verify admin user details
        admin_id = admin_user.get('id')
        admin_name = admin_user.get('name')
        admin_role = admin_user.get('role')
        admin_active = admin_user.get('is_active')
        
        print(f"   🆔 Admin ID: {admin_id}")
        print(f"   👤 Admin Name: {admin_name}")
        print(f"   🔰 Admin Role: {admin_role}")
        print(f"   ✅ Admin Active: {admin_active}")
        
        # Verify role is 'owner' for deletion permissions
        has_owner_role = admin_role == 'owner'
        is_active = admin_active is True
        
        success = admin_user is not None and has_owner_role and is_active
        
        self.log_test("Admin User Verification", success, 
                     f"- Role: {admin_role}, Active: {admin_active}")
        return success

    def test_create_test_users_for_deletion(self):
        """Create test users for deletion testing"""
        print("\n👤 CREATING TEST USERS FOR DELETION")
        
        if not self.admin_token:
            self.log_test("Create Test Users", False, "- No admin token available")
            return False
            
        test_users_data = [
            {
                "email": f"test_delete_1_{datetime.now().strftime('%H%M%S')}@example.com",
                "name": "Test Delete User 1",
                "password": "TestPass123!",
                "role": "teacher"
            },
            {
                "email": f"test_delete_2_{datetime.now().strftime('%H%M%S')}@example.com",
                "name": "Test Delete User 2", 
                "password": "TestPass123!",
                "role": "manager"
            }
        ]
        
        created_users = []
        
        for user_data in test_users_data:
            success, response = self.make_request('POST', 'users', user_data, 200)
            
            if success:
                user_id = response.get('id')
                created_users.append({
                    'id': user_id,
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data['role']
                })
                self.test_user_ids.append(user_id)
                print(f"   ✅ Created: {user_data['name']} (ID: {user_id[:8]}...)")
            else:
                print(f"   ❌ Failed to create: {user_data['name']}")
                
        success = len(created_users) == len(test_users_data)
        
        self.log_test("Create Test Users", success, 
                     f"- Created {len(created_users)}/{len(test_users_data)} test users")
        return success

    def test_user_deletion_with_valid_ids(self):
        """Test DELETE /api/users/{user_id} with valid user IDs"""
        print("\n🗑️  TESTING USER DELETION WITH VALID IDs")
        
        if not self.test_user_ids:
            self.log_test("User Deletion (Valid IDs)", False, "- No test users available")
            return False
            
        if not self.admin_token:
            self.log_test("User Deletion (Valid IDs)", False, "- No admin token available")
            return False
            
        successful_deletions = 0
        failed_deletions = 0
        
        for user_id in self.test_user_ids:
            print(f"   🎯 Attempting to delete user: {user_id[:8]}...")
            
            success, response = self.make_request('DELETE', f'users/{user_id}', expected_status=200)
            
            if success:
                successful_deletions += 1
                message = response.get('message', 'No message')
                print(f"   ✅ Deleted successfully: {message}")
            else:
                failed_deletions += 1
                error_detail = response.get('detail', 'Unknown error')
                status_code = response.get('status_code', 'Unknown')
                print(f"   ❌ Deletion failed: {error_detail} (Status: {status_code})")
                
                # Check if it's the "User not found" error we're investigating
                if 'not found' in error_detail.lower():
                    print(f"   🚨 FOUND THE ISSUE: 'User not found' error for ID {user_id}")
                    
        success = successful_deletions > 0
        
        self.log_test("User Deletion (Valid IDs)", success, 
                     f"- Success: {successful_deletions}, Failed: {failed_deletions}")
        return success

    def test_user_deletion_with_invalid_ids(self):
        """Test DELETE /api/users/{user_id} with invalid user IDs"""
        print("\n🚫 TESTING USER DELETION WITH INVALID IDs")
        
        if not self.admin_token:
            self.log_test("User Deletion (Invalid IDs)", False, "- No admin token available")
            return False
            
        invalid_ids = [
            "nonexistent-user-id",
            "12345678-1234-1234-1234-123456789012",  # Valid UUID format but nonexistent
            "507f1f77bcf86cd799439011",  # Valid ObjectId format but nonexistent
            "",  # Empty string
            "invalid-format"
        ]
        
        expected_404_count = 0
        
        for invalid_id in invalid_ids:
            print(f"   🎯 Testing invalid ID: '{invalid_id}'")
            
            success, response = self.make_request('DELETE', f'users/{invalid_id}', expected_status=404)
            
            if success:
                expected_404_count += 1
                print(f"   ✅ Correctly returned 404 for invalid ID")
            else:
                status_code = response.get('status_code', 'Unknown')
                error_detail = response.get('detail', 'Unknown error')
                print(f"   ❌ Unexpected response: {error_detail} (Status: {status_code})")
                
        success = expected_404_count == len(invalid_ids)
        
        self.log_test("User Deletion (Invalid IDs)", success, 
                     f"- Expected 404s: {expected_404_count}/{len(invalid_ids)}")
        return success

    def test_user_deletion_permissions(self):
        """Test user deletion with different permission levels"""
        print("\n🔐 TESTING USER DELETION PERMISSIONS")
        
        # Test 1: Owner role (should work)
        print("   Testing owner role permissions...")
        
        # Create a test user to delete
        test_user_data = {
            "email": f"perm_test_{datetime.now().strftime('%H%M%S')}@example.com",
            "name": "Permission Test User",
            "password": "TestPass123!",
            "role": "teacher"
        }
        
        success, response = self.make_request('POST', 'users', test_user_data, 200)
        if not success:
            self.log_test("User Deletion Permissions", False, "- Failed to create test user")
            return False
            
        test_user_id = response.get('id')
        
        # Try to delete as owner (should work)
        success, response = self.make_request('DELETE', f'users/{test_user_id}', expected_status=200)
        
        owner_can_delete = success
        if success:
            print("   ✅ Owner can delete users")
        else:
            print(f"   ❌ Owner cannot delete users: {response.get('detail', 'Unknown error')}")
            
        # Test 2: Self-deletion prevention
        print("   Testing self-deletion prevention...")
        
        success, response = self.make_request('DELETE', f'users/{self.admin_user_id}', expected_status=400)
        
        self_deletion_prevented = success
        if success:
            print("   ✅ Self-deletion correctly prevented")
        else:
            print(f"   ❌ Self-deletion not prevented: {response.get('detail', 'Unknown error')}")
            
        overall_success = owner_can_delete and self_deletion_prevented
        
        self.log_test("User Deletion Permissions", overall_success, 
                     f"- Owner: {'✓' if owner_can_delete else '✗'}, Self-prevention: {'✓' if self_deletion_prevented else '✗'}")
        return overall_success

    def test_database_user_investigation(self):
        """Investigate user data in database through API"""
        print("\n🔍 INVESTIGATING USER DATABASE DATA")
        
        if not self.all_users:
            self.log_test("Database User Investigation", False, "- No users available")
            return False
            
        print("   📊 User Data Analysis:")
        
        # Analyze user data structure
        required_fields = ['id', 'name', 'email', 'role', 'is_active']
        optional_fields = ['created_at', 'updated_at', 'studio_name']
        
        users_with_all_required = 0
        users_with_missing_fields = 0
        missing_fields_summary = {}
        
        for user in self.all_users:
            has_all_required = all(field in user for field in required_fields)
            
            if has_all_required:
                users_with_all_required += 1
            else:
                users_with_missing_fields += 1
                for field in required_fields:
                    if field not in user:
                        missing_fields_summary[field] = missing_fields_summary.get(field, 0) + 1
                        
        print(f"   ✅ Users with all required fields: {users_with_all_required}")
        print(f"   ❌ Users with missing fields: {users_with_missing_fields}")
        
        if missing_fields_summary:
            print("   📋 Missing fields summary:")
            for field, count in missing_fields_summary.items():
                print(f"      {field}: missing in {count} users")
                
        # Check for data inconsistencies
        active_users = sum(1 for user in self.all_users if user.get('is_active', False))
        inactive_users = len(self.all_users) - active_users
        
        print(f"   📈 Active users: {active_users}")
        print(f"   📉 Inactive users: {inactive_users}")
        
        # Check role distribution
        role_distribution = {}
        for user in self.all_users:
            role = user.get('role', 'unknown')
            role_distribution[role] = role_distribution.get(role, 0) + 1
            
        print("   🔰 Role distribution:")
        for role, count in role_distribution.items():
            print(f"      {role}: {count}")
            
        success = users_with_all_required > 0
        
        self.log_test("Database User Investigation", success, 
                     f"- Complete users: {users_with_all_required}, Issues: {users_with_missing_fields}")
        return success

    def test_authentication_token_validation(self):
        """Test authentication and token validation for user endpoints"""
        print("\n🔑 TESTING AUTHENTICATION & TOKEN VALIDATION")
        
        # Test 1: No token
        print("   Testing without authentication token...")
        original_token = self.admin_token
        self.admin_token = None
        
        success, response = self.make_request('GET', 'users', expected_status=401)
        no_token_rejected = success
        
        if success:
            print("   ✅ Request without token correctly rejected (401)")
        else:
            print(f"   ❌ Request without token not rejected: {response.get('detail', 'Unknown')}")
            
        # Test 2: Invalid token
        print("   Testing with invalid token...")
        self.admin_token = "invalid.token.here"
        
        success, response = self.make_request('GET', 'users', expected_status=401)
        invalid_token_rejected = success
        
        if success:
            print("   ✅ Request with invalid token correctly rejected (401)")
        else:
            print(f"   ❌ Request with invalid token not rejected: {response.get('detail', 'Unknown')}")
            
        # Test 3: Valid token
        print("   Testing with valid token...")
        self.admin_token = original_token
        
        success, response = self.make_request('GET', 'users', expected_status=200)
        valid_token_accepted = success
        
        if success:
            print("   ✅ Request with valid token correctly accepted (200)")
        else:
            print(f"   ❌ Request with valid token rejected: {response.get('detail', 'Unknown')}")
            
        overall_success = no_token_rejected and invalid_token_rejected and valid_token_accepted
        
        self.log_test("Authentication & Token Validation", overall_success,
                     f"- No token: {'✓' if no_token_rejected else '✗'}, Invalid: {'✓' if invalid_token_rejected else '✗'}, Valid: {'✓' if valid_token_accepted else '✗'}")
        return overall_success

    def run_comprehensive_user_management_tests(self):
        """Run all user management tests"""
        print("🚀 STARTING COMPREHENSIVE USER MANAGEMENT SYSTEM TESTING")
        print("=" * 80)
        
        # Authentication tests
        if not self.test_admin_authentication():
            print("❌ Cannot proceed without admin authentication")
            return False
            
        # User listing and investigation tests
        self.test_get_all_users()
        self.test_user_id_format_verification()
        self.test_admin_user_verification()
        self.test_database_user_investigation()
        
        # Authentication and permission tests
        self.test_authentication_token_validation()
        
        # User deletion tests
        self.test_create_test_users_for_deletion()
        self.test_user_deletion_with_valid_ids()
        self.test_user_deletion_with_invalid_ids()
        self.test_user_deletion_permissions()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED - CHECK DETAILS ABOVE")
            
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = UserManagementTester()
    success = tester.run_comprehensive_user_management_tests()
    sys.exit(0 if success else 1)