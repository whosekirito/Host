
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'your-supabase-url')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'your-supabase-key')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'your-supabase-service-key')

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Email Configuration
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', 'your-gmail-app-password')
ADMIN_EMAIL = 'whosekirito@gmail.com'

# File Upload Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'zip', 'rar', 
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'py', 'js', 'html', 'css'
}

# Storage Configuration
STORAGE_BUCKET = 'oppai-files'
MAX_FILES_PER_USER = {
    'free': 1,
    'basic': 10,
    'premium': 50,
    'pro': 200
}

# Pricing Configuration (in Indian Rupees)
PLAN_PRICES = {
    'free': 0,
    'basic': 299,
    'premium': 799,
    'pro': 1999
}

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
