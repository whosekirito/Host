#!/usr/bin/env python3
"""
Test script for Oppai Xd file hosting platform
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from app import app, generate_user_id, allowed_file, get_user_plan
        print("✅ Main app imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    try:
        from config import SUPABASE_URL, SUPABASE_KEY, PLAN_PRICES, MAX_FILES_PER_USER
        print("✅ Config imports successful")
    except ImportError as e:
        print(f"❌ Config import error: {e}")
        return False
    
    return True

def test_user_id_generation():
    """Test user ID generation"""
    print("🧪 Testing user ID generation...")
    
    from app import generate_user_id
    
    # Generate multiple user IDs
    user_ids = [generate_user_id() for _ in range(10)]
    
    # Check if all are unique
    if len(set(user_ids)) == len(user_ids):
        print("✅ User ID generation working correctly")
        return True
    else:
        print("❌ User ID generation failed - duplicates found")
        return False

def test_file_validation():
    """Test file validation"""
    print("🧪 Testing file validation...")
    
    from app import allowed_file
    
    # Test valid files
    valid_files = ['test.txt', 'image.jpg', 'document.pdf', 'video.mp4']
    for filename in valid_files:
        if not allowed_file(filename):
            print(f"❌ File validation failed for {filename}")
            return False
    
    # Test invalid files
    invalid_files = ['test.exe', 'script.bat', 'malware.vbs']
    for filename in invalid_files:
        if allowed_file(filename):
            print(f"❌ File validation failed - {filename} should be rejected")
            return False
    
    print("✅ File validation working correctly")
    return True

def test_flask_app():
    """Test Flask app creation"""
    print("🧪 Testing Flask app creation...")
    
    try:
        from app import app
        
        # Test if app is created
        if app is not None:
            print("✅ Flask app created successfully")
            
            # Test if routes are registered
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            expected_routes = ['/', '/login', '/register', '/dashboard', '/plans', '/admin']
            
            for route in expected_routes:
                if route in routes:
                    print(f"✅ Route {route} registered")
                else:
                    print(f"❌ Route {route} not found")
                    return False
            
            return True
        else:
            print("❌ Flask app creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_config_values():
    """Test configuration values"""
    print("🧪 Testing configuration values...")
    
    from config import PLAN_PRICES, MAX_FILES_PER_USER, ALLOWED_EXTENSIONS
    
    # Test plan prices
    expected_plans = ['free', 'basic', 'premium', 'pro']
    for plan in expected_plans:
        if plan not in PLAN_PRICES:
            print(f"❌ Plan {plan} not found in pricing")
            return False
    
    # Test max files
    for plan in expected_plans:
        if plan not in MAX_FILES_PER_USER:
            print(f"❌ Plan {plan} not found in max files")
            return False
    
    # Test allowed extensions
    if len(ALLOWED_EXTENSIONS) == 0:
        print("❌ No allowed extensions configured")
        return False
    
    print("✅ Configuration values are correct")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Oppai Xd application tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_user_id_generation,
        test_file_validation,
        test_flask_app,
        test_config_values
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n📋 Next steps:")
        print("1. Set up Supabase database")
        print("2. Configure .env file")
        print("3. Run: python3 app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()