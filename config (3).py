
import os

# Bot configuration
BOT_TOKEN = "8202785686:AAHYVCcuL_AyGiZikBE1pw2ldDKuqOYMNsA"
UPLOAD_FOLDER = "uploaded_bots"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = ['.py', '.js', '.zip']

# Flask configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
DEBUG = False

# Bot limits per user
MAX_BOTS_PER_USER = 5
MAX_BOT_MEMORY = 512  # MB
MAX_BOT_CPU = 50  # Percentage

# Monitoring settings
HEALTH_CHECK_INTERVAL = 30  # seconds
AUTO_RESTART_ENABLED = True
LOG_RETENTION_DAYS = 7

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, UPLOAD_FOLDER)
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
