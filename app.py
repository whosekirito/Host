from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import random
import string
from datetime import datetime, timedelta
import json
import io
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client
from config import *
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.warning(f"Supabase client initialization failed: {e}")
    supabase = None

def generate_user_id():
    """Generate a random user ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def is_gmail(email):
    """Check if email is from Gmail"""
    return email.lower().endswith('@gmail.com')

def send_verification_email(email, verification_code):
    """Send verification email"""
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "whosekirito@gmail.com"
        sender_password = os.getenv('GMAIL_APP_PASSWORD', 'your-app-password')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Verify Your Oppai Xd Account"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Welcome to Oppai Xd!</h2>
            <p>Thank you for registering. Please verify your email address by entering the following code:</p>
            <h1 style="color: #6366f1; text-align: center; font-size: 2em;">{verification_code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Oppai Xd Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_plan(user_id):
    """Get user's current plan"""
    if not supabase:
        return 'free'
    try:
        result = supabase.table('users').select('plan').eq('user_id', user_id).execute()
        if result.data:
            return result.data[0]['plan']
        return 'free'
    except Exception as e:
        logger.error(f"Error getting user plan: {e}")
        return 'free'

def get_user_files_count(user_id):
    """Get count of files uploaded by user"""
    if not supabase:
        return 0
    try:
        result = supabase.table('files').select('id').eq('user_id', user_id).execute()
        return len(result.data)
    except Exception as e:
        logger.error(f"Error getting user files count: {e}")
        return 0

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Validate Gmail only
        if not is_gmail(email):
            flash('Only Gmail addresses are allowed for registration!', 'error')
            return render_template('register.html')
        
        # Generate random user ID
        user_id = generate_user_id()
        
        try:
            # Check if email already exists
            existing_user = supabase.table('users').select('id').eq('email', email).execute()
            if existing_user.data:
                flash('Email already registered!', 'error')
                return render_template('register.html')
            
            # Generate verification code
            verification_code = generate_verification_code()
            verification_expires = datetime.now() + timedelta(minutes=10)
            
            # Create user (unverified initially)
            user_data = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'password': generate_password_hash(password),
                'plan': 'free',
                'is_verified': False,
                'verification_code': verification_code,
                'verification_expires': verification_expires.isoformat(),
                'is_admin': False,
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase.table('users').insert(user_data).execute()
            
            if result.data:
                # Send verification email
                if send_verification_email(email, verification_code):
                    session['user_id'] = user_id
                    session['username'] = username
                    session['plan'] = 'free'
                    session['is_verified'] = False
                    flash('Registration successful! Please check your email for verification code.', 'success')
                    return redirect(url_for('verify_email'))
                else:
                    flash('Registration successful but email verification failed. Please contact support.', 'warning')
                    return redirect(url_for('verify_email'))
            else:
                flash('Registration failed!', 'error')
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('Registration failed! Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            # Get user by email
            result = supabase.table('users').select('*').eq('email', email).execute()
            
            if result.data and check_password_hash(result.data[0]['password'], password):
                user = result.data[0]
                
                # Check if email is verified
                if not user.get('is_verified', False):
                    session['user_id'] = user['user_id']
                    session['username'] = user['username']
                    session['plan'] = user['plan']
                    session['is_verified'] = False
                    flash('Please verify your email before logging in!', 'warning')
                    return redirect(url_for('verify_email'))
                
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['plan'] = user['plan']
                session['is_verified'] = user.get('is_verified', False)
                session['is_admin'] = user.get('is_admin', False)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password!', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login failed! Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    """Email verification page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        verification_code = request.form['verification_code']
        user_id = session['user_id']
        
        try:
            # Get user verification data
            result = supabase.table('users').select('verification_code, verification_expires, is_verified').eq('user_id', user_id).execute()
            
            if result.data:
                user = result.data[0]
                
                # Check if already verified
                if user['is_verified']:
                    flash('Email already verified!', 'success')
                    return redirect(url_for('dashboard'))
                
                # Check if code matches and not expired
                if (user['verification_code'] == verification_code and 
                    datetime.now() < datetime.fromisoformat(user['verification_expires'])):
                    
                    # Update user as verified
                    supabase.table('users').update({
                        'is_verified': True,
                        'verification_code': None,
                        'verification_expires': None
                    }).eq('user_id', user_id).execute()
                    
                    session['is_verified'] = True
                    flash('Email verified successfully!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid or expired verification code!', 'error')
            else:
                flash('User not found!', 'error')
                
        except Exception as e:
            logger.error(f"Verification error: {e}")
            flash('Verification failed! Please try again.', 'error')
    
    return render_template('verify_email.html')

@app.route('/resend_verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    try:
        # Get user email
        result = supabase.table('users').select('email, is_verified').eq('user_id', user_id).execute()
        
        if result.data:
            user = result.data[0]
            
            if user['is_verified']:
                return jsonify({'error': 'Email already verified'}), 400
            
            # Generate new verification code
            verification_code = generate_verification_code()
            verification_expires = datetime.now() + timedelta(minutes=10)
            
            # Update verification code
            supabase.table('users').update({
                'verification_code': verification_code,
                'verification_expires': verification_expires.isoformat()
            }).eq('user_id', user_id).execute()
            
            # Send email
            if send_verification_email(user['email'], verification_code):
                return jsonify({'success': 'Verification email sent!'})
            else:
                return jsonify({'error': 'Failed to send email'}), 500
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        return jsonify({'error': 'Failed to resend verification'}), 500

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

def create_admin_user():
    """Create admin user if not exists"""
    try:
        # Check if admin exists
        result = supabase.table('users').select('id').eq('email', 'whosekirito@gmail.com').execute()
        
        if not result.data:
            # Create admin user
            admin_data = {
                'user_id': 'admin',
                'username': 'Admin',
                'email': 'whosekirito@gmail.com',
                'password': generate_password_hash('admin123'),  # Change this password
                'plan': 'pro',
                'is_verified': True,
                'is_admin': True,
                'created_at': datetime.now().isoformat()
            }
            
            supabase.table('users').insert(admin_data).execute()
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if email is verified
    if not session.get('is_verified', False):
        flash('Please verify your email to access the dashboard!', 'warning')
        return redirect(url_for('verify_email'))
    
    user_id = session['user_id']
    plan = session.get('plan', 'free')
    
    # Get user files
    try:
        files_result = supabase.table('files').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        files = files_result.data if files_result.data else []
    except Exception as e:
        logger.error(f"Error getting user files: {e}")
        files = []
    
    files_count = len(files)
    max_files = MAX_FILES_PER_USER.get(plan, 1)
    
    return render_template('dashboard.html', 
                         files=files, 
                         plan=plan, 
                         files_count=files_count, 
                         max_files=max_files)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload file"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    plan = session.get('plan', 'free')
    
    # Check file limit
    current_files = get_user_files_count(user_id)
    max_files = MAX_FILES_PER_USER.get(plan, 1)
    
    if current_files >= max_files:
        return jsonify({'error': f'File limit reached! Upgrade to upload more files.'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Upload to Supabase Storage
            file_data = file.read()
            storage_result = supabase.storage.from_(STORAGE_BUCKET).upload(unique_filename, file_data)
            
            if storage_result:
                # Save file info to database
                file_info = {
                    'user_id': user_id,
                    'original_name': filename,
                    'stored_name': unique_filename,
                    'file_size': len(file_data),
                    'file_type': filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown',
                    'created_at': datetime.now().isoformat()
                }
                
                db_result = supabase.table('files').insert(file_info).execute()
                
                if db_result.data:
                    return jsonify({'success': 'File uploaded successfully!'})
                else:
                    # Clean up storage if DB insert failed
                    supabase.storage.from_(STORAGE_BUCKET).remove([unique_filename])
                    return jsonify({'error': 'Failed to save file info'}), 500
            else:
                return jsonify({'error': 'Failed to upload file'}), 500
                
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return jsonify({'error': 'Upload failed'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<file_id>')
def download_file(file_id):
    """Download file"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get file info
        result = supabase.table('files').select('*').eq('id', file_id).eq('user_id', session['user_id']).execute()
        
        if not result.data:
            flash('File not found!', 'error')
            return redirect(url_for('dashboard'))
        
        file_info = result.data[0]
        
        # Get file from storage
        file_data = supabase.storage.from_(STORAGE_BUCKET).download(file_info['stored_name'])
        
        if file_data:
            return send_file(
                io.BytesIO(file_data),
                as_attachment=True,
                download_name=file_info['original_name']
            )
        else:
            flash('File download failed!', 'error')
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        flash('Download failed!', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete/<file_id>')
def delete_file(file_id):
    """Delete file"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get file info
        result = supabase.table('files').select('*').eq('id', file_id).eq('user_id', session['user_id']).execute()
        
        if not result.data:
            flash('File not found!', 'error')
            return redirect(url_for('dashboard'))
        
        file_info = result.data[0]
        
        # Delete from storage
        supabase.storage.from_(STORAGE_BUCKET).remove([file_info['stored_name']])
        
        # Delete from database
        supabase.table('files').delete().eq('id', file_id).execute()
        
        flash('File deleted successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        flash('Delete failed!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/plans')
def plans():
    """Pricing plans page"""
    return render_template('plans.html', plans=PLAN_PRICES, max_files=MAX_FILES_PER_USER)

@app.route('/admin')
def admin():
    """Admin panel"""
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Check if user is admin
    try:
        result = supabase.table('users').select('is_admin').eq('user_id', session['user_id']).execute()
        if not result.data or not result.data[0]['is_admin']:
            flash('Access denied! Admin privileges required.', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Admin check error: {e}")
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get all users
        users_result = supabase.table('users').select('*').execute()
        users = users_result.data if users_result.data else []
        
        # Get all files
        files_result = supabase.table('files').select('*').execute()
        files = files_result.data if files_result.data else []
        
        # Get statistics
        stats = {
            'total_users': len(users),
            'total_files': len(files),
            'free_users': len([u for u in users if u['plan'] == 'free']),
            'premium_users': len([u for u in users if u['plan'] != 'free'])
        }
        
    except Exception as e:
        logger.error(f"Admin error: {e}")
        users = []
        files = []
        stats = {'total_users': 0, 'total_files': 0, 'free_users': 0, 'premium_users': 0}
    
    return render_template('admin.html', users=users, files=files, stats=stats, plans=PLAN_PRICES)

@app.route('/admin/update_plan', methods=['POST'])
def update_user_plan():
    """Update user plan (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user is admin
    try:
        result = supabase.table('users').select('is_admin').eq('user_id', session['user_id']).execute()
        if not result.data or not result.data[0]['is_admin']:
            return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        logger.error(f"Admin check error: {e}")
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    new_plan = data.get('plan')
    
    if not user_id or not new_plan:
        return jsonify({'error': 'Invalid data'}), 400
    
    try:
        result = supabase.table('users').update({'plan': new_plan}).eq('user_id', user_id).execute()
        
        if result.data:
            return jsonify({'success': 'Plan updated successfully!'})
        else:
            return jsonify({'error': 'Failed to update plan'}), 500
            
    except Exception as e:
        logger.error(f"Update plan error: {e}")
        return jsonify({'error': 'Update failed'}), 500

@app.route('/admin/update_pricing', methods=['POST'])
def update_pricing():
    """Update plan pricing (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user is admin
    try:
        result = supabase.table('users').select('is_admin').eq('user_id', session['user_id']).execute()
        if not result.data or not result.data[0]['is_admin']:
            return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        logger.error(f"Admin check error: {e}")
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    try:
        # Update pricing in database or config
        # For now, we'll just return success
        return jsonify({'success': 'Pricing updated successfully!'})
        
    except Exception as e:
        logger.error(f"Update pricing error: {e}")
        return jsonify({'error': 'Update failed'}), 500

if __name__ == '__main__':
    # Create admin user on startup
    create_admin_user()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG)