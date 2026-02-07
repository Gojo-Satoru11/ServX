"""
Application routes
All URL endpoints for the cloud storage application
"""

from flask import render_template, request, redirect, url_for, session, flash, send_from_directory, current_app
from functools import wraps
import os
import secrets
import shutil
from datetime import datetime

from database import (
    create_user, get_user, update_user_activity, update_user_storage,
    get_all_users, create_shared_folder as db_create_shared_folder,
    get_shared_folder, get_user_shared_folders, delete_shared_folder,
    can_access_folder
)
from utils import (
    hash_password, verify_password, allowed_file, format_file_size,
    get_directory_size, get_files_in_directory, safe_filename,
    ensure_directory_exists
)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_storage_path(username):
    """Get user's storage directory path"""
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], username)
    return ensure_directory_exists(path)

def get_shared_folder_path(folder_id):
    """Get shared folder path"""
    path = os.path.join(current_app.config['SHARED_FOLDER'], folder_id)
    return ensure_directory_exists(path)

def register_routes(app):
    """Register all routes with the app"""
    
    @app.route('/')
    def index():
        if 'username' in session:
            return redirect(url_for('storage'))
        return redirect(url_for('login'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            if not username or not email or not password:
                flash('All fields are required.', 'error')
                return render_template('register.html')
            
            if len(username) < 3:
                flash('Username must be at least 3 characters.', 'error')
                return render_template('register.html')
            
            if len(password) < 8:
                flash('Password must be at least 8 characters.', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            
            # Create user
            salt, hashed_password = hash_password(password)
            success, message = create_user(
                app.config['DATABASE_FILE'],
                username, email, salt, hashed_password,
                app.config['STORAGE_LIMIT_PER_USER']
            )
            
            if success:
                # Create user storage directory
                get_user_storage_path(username)
                flash(f'Registration successful! You have {app.config["STORAGE_LIMIT_PER_USER"]/(1024**3):.0f}GB of storage. Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'error')
                return render_template('register.html')
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'username' in session:
            return redirect(url_for('storage'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Please enter both username and password.', 'error')
                return render_template('login.html')
            
            user = get_user(app.config['DATABASE_FILE'], username)
            
            if not user:
                flash('Invalid username or password.', 'error')
                return render_template('login.html')
            
            if verify_password(user['salt'], user['password'], password):
                session.permanent = True
                session['username'] = username
                session['login_time'] = datetime.now().isoformat()
                update_user_activity(app.config['DATABASE_FILE'], username)
                flash(f'Welcome back, {username}!', 'success')
                return redirect(url_for('storage'))
            else:
                flash('Invalid username or password.', 'error')
                return render_template('login.html')
        
        return render_template('login.html')
    
    @app.route('/storage')
    @login_required
    def storage():
        username = session['username']
        user_path = get_user_storage_path(username)
        files = get_files_in_directory(user_path)
        
        # Calculate storage
        storage_used = get_directory_size(user_path)
        storage_limit = app.config['STORAGE_LIMIT_PER_USER']
        storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
        
        update_user_storage(app.config['DATABASE_FILE'], username, storage_used)
        
        return render_template('storage.html',
                             username=username,
                             files=files,
                             file_count=len(files),
                             storage_used=format_file_size(storage_used),
                             storage_limit=format_file_size(storage_limit),
                             storage_percent=storage_percent,
                             storage_used_bytes=storage_used,
                             storage_limit_bytes=storage_limit)
    
    @app.route('/upload', methods=['POST'])
    @login_required
    def upload_file():
        username = session['username']
        
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(url_for('storage'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('storage'))
        
        if not allowed_file(file.filename):
            flash('File type not allowed.', 'error')
            return redirect(url_for('storage'))
        
        # Check storage limit
        user_path = get_user_storage_path(username)
        storage_used = get_directory_size(user_path)
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if storage_used + file_size > app.config['STORAGE_LIMIT_PER_USER']:
            flash(f'Not enough storage space.', 'error')
            return redirect(url_for('storage'))
        
        # Save file
        filename = safe_filename(file.filename)
        filepath = os.path.join(user_path, filename)
        
        # Handle duplicates
        counter = 1
        while os.path.exists(filepath):
            filename = safe_filename(file.filename, counter)
            filepath = os.path.join(user_path, filename)
            counter += 1
        
        file.save(filepath)
        flash(f'File "{filename}" uploaded successfully! ({format_file_size(file_size)})', 'success')
        return redirect(url_for('storage'))
    
    @app.route('/download/<path:filename>')
    @login_required
    def download_file(filename):
        username = session['username']
        user_path = get_user_storage_path(username)
        filename = os.path.basename(filename)
        
        if not os.path.exists(os.path.join(user_path, filename)):
            flash('File not found.', 'error')
            return redirect(url_for('storage'))
        
        try:
            return send_from_directory(user_path, filename, as_attachment=True)
        except Exception as e:
            app.logger.error(f'Download error: {str(e)}')
            flash('Error downloading file.', 'error')
            return redirect(url_for('storage'))
    
    @app.route('/delete/<path:filename>', methods=['POST'])
    @login_required
    def delete_file(filename):
        username = session['username']
        user_path = get_user_storage_path(username)
        filename = os.path.basename(filename)
        filepath = os.path.join(user_path, filename)
        
        if not os.path.exists(filepath):
            flash('File not found.', 'error')
            return redirect(url_for('storage'))
        
        os.remove(filepath)
        flash(f'File "{filename}" deleted successfully.', 'success')
        return redirect(url_for('storage'))
    
    # Shared folders routes
    @app.route('/shared')
    @login_required
    def shared_folders():
        username = session['username']
        folders = get_user_shared_folders(app.config['DATABASE_FILE'], username)
        
        # Add file counts
        for folder in folders:
            folder_path = get_shared_folder_path(folder['id'])
            folder['file_count'] = len(get_files_in_directory(folder_path))
        
        all_users = [u for u in get_all_users(app.config['DATABASE_FILE']).keys() if u != username]
        
        return render_template('shared.html',
                             username=username,
                             folders=folders,
                             all_users=all_users)
    
    @app.route('/create_shared_folder', methods=['POST'])
    @login_required
    def create_folder():
        username = session['username']
        folder_name = request.form.get('folder_name', '').strip()
        shared_with_users = request.form.getlist('shared_with')
        
        if not folder_name:
            flash('Please enter a folder name.', 'error')
            return redirect(url_for('shared_folders'))
        
        if not shared_with_users:
            flash('Please select at least one user to share with.', 'error')
            return redirect(url_for('shared_folders'))
        
        folder_id = secrets.token_hex(8)
        db_create_shared_folder(app.config['DATABASE_FILE'], folder_id, folder_name, username, shared_with_users)
        get_shared_folder_path(folder_id)
        
        flash(f'Shared folder "{folder_name}" created successfully!', 'success')
        return redirect(url_for('view_shared_folder', folder_id=folder_id))
    
    @app.route('/shared/<folder_id>')
    @login_required
    def view_shared_folder(folder_id):
        username = session['username']
        
        if not can_access_folder(app.config['DATABASE_FILE'], username, folder_id):
            flash('You do not have access to this folder.', 'error')
            return redirect(url_for('shared_folders'))
        
        folder_info = get_shared_folder(app.config['DATABASE_FILE'], folder_id)
        folder_path = get_shared_folder_path(folder_id)
        files = get_files_in_directory(folder_path)
        
        return render_template('shared_folder.html',
                             username=username,
                             folder_id=folder_id,
                             folder_name=folder_info['name'],
                             is_owner=folder_info['owner'] == username,
                             owner=folder_info['owner'],
                             shared_with=folder_info['shared_with'],
                             files=files,
                             file_count=len(files))
    
    @app.route('/upload_to_shared/<folder_id>', methods=['POST'])
    @login_required
    def upload_to_shared(folder_id):
        username = session['username']
        
        if not can_access_folder(app.config['DATABASE_FILE'], username, folder_id):
            flash('You do not have access to this folder.', 'error')
            return redirect(url_for('shared_folders'))
        
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(url_for('view_shared_folder', folder_id=folder_id))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('view_shared_folder', folder_id=folder_id))
        
        if not allowed_file(file.filename):
            flash('File type not allowed.', 'error')
            return redirect(url_for('view_shared_folder', folder_id=folder_id))
        
        # Save file
        folder_path = get_shared_folder_path(folder_id)
        filename = safe_filename(file.filename)
        filepath = os.path.join(folder_path, filename)
        
        counter = 1
        while os.path.exists(filepath):
            filename = safe_filename(file.filename, counter)
            filepath = os.path.join(folder_path, filename)
            counter += 1
        
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        flash(f'File "{filename}" uploaded to shared folder! ({format_file_size(file_size)})', 'success')
        return redirect(url_for('view_shared_folder', folder_id=folder_id))
    
    @app.route('/download_shared/<folder_id>/<path:filename>')
    @login_required
    def download_shared_file(folder_id, filename):
        username = session['username']
        
        if not can_access_folder(app.config['DATABASE_FILE'], username, folder_id):
            flash('You do not have access to this folder.', 'error')
            return redirect(url_for('shared_folders'))
        
        folder_path = get_shared_folder_path(folder_id)
        filename = os.path.basename(filename)
        
        if not os.path.exists(os.path.join(folder_path, filename)):
            flash('File not found.', 'error')
            return redirect(url_for('view_shared_folder', folder_id=folder_id))
        
        try:
            return send_from_directory(folder_path, filename, as_attachment=True)
        except Exception as e:
            app.logger.error(f'Download error: {str(e)}')
            flash('Error downloading file.', 'error')
            return redirect(url_for('view_shared_folder', folder_id=folder_id))
    
    @app.route('/delete_shared/<folder_id>/<path:filename>', methods=['POST'])
    @login_required
    def delete_shared_file(folder_id, filename):
        username = session['username']
        
        if not can_access_folder(app.config['DATABASE_FILE'], username, folder_id):
            flash('You do not have access to this folder.', 'error')
            return redirect(url_for('shared_folders'))
        
        folder_path = get_shared_folder_path(folder_id)
        filename = os.path.basename(filename)
        filepath = os.path.join(folder_path, filename)
        
        if not os.path.exists(filepath):
            flash('File not found.', 'error')
            return redirect(url_for('view_shared_folder', folder_id=folder_id))
        
        os.remove(filepath)
        flash(f'File "{filename}" deleted from shared folder.', 'success')
        return redirect(url_for('view_shared_folder', folder_id=folder_id))
    
    @app.route('/delete_shared_folder/<folder_id>', methods=['POST'])
    @login_required
    def delete_folder(folder_id):
        username = session['username']
        folder_info = get_shared_folder(app.config['DATABASE_FILE'], folder_id)
        
        if not folder_info:
            flash('Folder not found.', 'error')
            return redirect(url_for('shared_folders'))
        
        if folder_info['owner'] != username:
            flash('Only the folder owner can delete this folder.', 'error')
            return redirect(url_for('shared_folders'))
        
        # Delete physical folder
        folder_path = get_shared_folder_path(folder_id)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        
        # Delete from database
        delete_shared_folder(app.config['DATABASE_FILE'], folder_id)
        
        flash(f'Shared folder "{folder_info["name"]}" deleted successfully.', 'success')
        return redirect(url_for('shared_folders'))
    
    @app.route('/account')
    @login_required
    def account():
        username = session['username']
        user = get_user(app.config['DATABASE_FILE'], username)
        user_path = get_user_storage_path(username)
        
        storage_used = get_directory_size(user_path)
        file_count = len(get_files_in_directory(user_path))
        
        return render_template('account.html',
                             username=username,
                             email=user['email'],
                             created_at=user['created_at'],
                             storage_used=format_file_size(storage_used),
                             storage_limit=format_file_size(app.config['STORAGE_LIMIT_PER_USER']),
                             file_count=file_count)
    
    @app.route('/logout')
    @login_required
    def logout():
        username = session.get('username')
        session.clear()
        flash(f'Goodbye, {username}!', 'success')
        return redirect(url_for('login'))
