#!/usr/bin/env python3
"""
Verification script for Oppai Xd file hosting platform
"""

import os
import sys
from pathlib import Path

def check_files():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'config.py',
        'database_schema.sql',
        'setup.py',
        'requirements.txt',
        '.env.example',
        'README.md'
    ]
    
    template_files = [
        'templates/base.html',
        'templates/index.html',
        'templates/login.html',
        'templates/register.html',
        'templates/dashboard.html',
        'templates/plans.html',
        'templates/admin.html'
    ]
    
    print("📁 Checking required files...")
    all_good = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            all_good = False
    
    print("\n📄 Checking template files...")
    for file in template_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            all_good = False
    
    return all_good

def check_directories():
    """Check if required directories exist"""
    required_dirs = [
        'templates',
        'static',
        'uploads',
        'logs'
    ]
    
    print("\n📂 Checking directories...")
    all_good = True
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}/")
        else:
            print(f"  ❌ {directory}/ - MISSING")
            all_good = False
    
    return all_good

def check_imports():
    """Check if Python imports work"""
    print("\n🐍 Checking Python imports...")
    all_good = True
    
    try:
        import flask
        print("  ✅ Flask")
    except ImportError:
        print("  ❌ Flask - NOT INSTALLED")
        all_good = False
    
    try:
        import supabase
        print("  ✅ Supabase")
    except ImportError:
        print("  ❌ Supabase - NOT INSTALLED")
        all_good = False
    
    try:
        import werkzeug
        print("  ✅ Werkzeug")
    except ImportError:
        print("  ❌ Werkzeug - NOT INSTALLED")
        all_good = False
    
    try:
        import app
        print("  ✅ App module")
    except Exception as e:
        print(f"  ❌ App module - ERROR: {e}")
        all_good = False
    
    return all_good

def check_config():
    """Check configuration"""
    print("\n⚙️  Checking configuration...")
    
    if os.path.exists('.env'):
        print("  ✅ .env file exists")
        with open('.env', 'r') as f:
            content = f.read()
            if 'your-supabase-url-here' in content:
                print("  ⚠️  .env needs Supabase credentials")
            else:
                print("  ✅ .env appears configured")
    else:
        print("  ❌ .env file missing")
    
    if os.path.exists('config.py'):
        print("  ✅ config.py exists")
    else:
        print("  ❌ config.py missing")

def main():
    """Main verification function"""
    print("🔍 Verifying Oppai Xd setup...")
    print("=" * 50)
    
    files_ok = check_files()
    dirs_ok = check_directories()
    imports_ok = check_imports()
    check_config()
    
    print("\n" + "=" * 50)
    
    if files_ok and dirs_ok and imports_ok:
        print("✅ All checks passed! Setup is complete.")
        print("\n📋 Next steps:")
        print("1. Configure Supabase credentials in .env file")
        print("2. Run database_schema.sql in Supabase")
        print("3. Start the application: python3 app.py")
        return True
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)