#!/usr/bin/env python3
"""
Setup script for Oppai Xd file hosting platform
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
        with open('.env.example', 'r') as f:
            content = f.read()
        with open('.env', 'w') as f:
            f.write(content)
        print("✅ .env file created! Please update it with your Supabase credentials.")
        return True
    else:
        print("ℹ️ .env file already exists.")
        return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ['uploads', 'static', 'templates', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✅ Directories created!")

def main():
    """Main setup function"""
    print("🚀 Setting up Oppai Xd file hosting platform...")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your Supabase credentials")
    print("2. Set up your Supabase database using database_schema.sql")
    print("3. Run: python app.py")
    print("\n🔗 Supabase setup:")
    print("1. Go to https://supabase.com")
    print("2. Create a new project")
    print("3. Go to Settings > API to get your keys")
    print("4. Go to Storage to create a bucket named 'oppai-files'")
    print("5. Run the SQL from database_schema.sql in the SQL editor")

if __name__ == "__main__":
    main()