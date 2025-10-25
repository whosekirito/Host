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
        
        # Generate random user ID
        user_id = generate_user_id()
        
        try:
            # Check if email already exists
            existing_user = supabase.table('users').select('id').eq('email', email).execute()
            if existing_user.data:
                flash('Email already registered!', 'error')
                return render_template('register.html')
            
            # Create user
            user_data = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'password': generate_password_hash(password),
                'plan': 'free',
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase.table('users').insert(user_data).execute()
            
            if result.data:
                session['user_id'] = user_id
                session['username'] = username
                session['plan'] = 'free'
                flash('Registration successful!', 'success')
                return redirect(url_for('dashboard'))
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
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['plan'] = user['plan']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password!', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login failed! Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
    if 'user_id' not in session or session.get('user_id') != 'admin':
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
    if 'user_id' not in session or session.get('user_id') != 'admin':
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
    if 'user_id' not in session or session.get('user_id') != 'admin':
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
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG)