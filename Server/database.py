"""
Database management module
Handles user data and shared folders
"""

import json
import os
from datetime import datetime

def init_db(db_file):
    """Initialize database file"""
    if not os.path.exists(db_file):
        with open(db_file, 'w') as f:
            json.dump({'users': {}, 'shared_folders': {}}, f, indent=2)

def load_db(db_file):
    """Load database"""
    try:
        with open(db_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        init_db(db_file)
        return {'users': {}, 'shared_folders': {}}

def save_db(db_file, data):
    """Save database"""
    # Create backup before saving
    if os.path.exists(db_file):
        backup_file = f"{db_file}.backup"
        try:
            with open(db_file, 'r') as f:
                backup_data = f.read()
            with open(backup_file, 'w') as f:
                f.write(backup_data)
        except:
            pass
    
    # Save new data
    with open(db_file, 'w') as f:
        json.dump(data, f, indent=2)

def create_user(db_file, username, email, salt, hashed_password, storage_limit):
    """Create a new user"""
    data = load_db(db_file)
    
    if username in data['users']:
        return False, "Username already exists"
    
    if len(data['users']) >= 10:  # Can be made configurable
        return False, "Maximum number of users reached"
    
    data['users'][username] = {
        'email': email,
        'salt': salt,
        'password': hashed_password,
        'created_at': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat(),
        'storage_used': 0,
        'storage_limit': storage_limit
    }
    
    save_db(db_file, data)
    return True, "User created successfully"

def get_user(db_file, username):
    """Get user data"""
    data = load_db(db_file)
    return data['users'].get(username)

def update_user_activity(db_file, username):
    """Update user's last active time"""
    data = load_db(db_file)
    if username in data['users']:
        data['users'][username]['last_active'] = datetime.now().isoformat()
        save_db(db_file, data)

def update_user_storage(db_file, username, storage_used):
    """Update user's storage usage"""
    data = load_db(db_file)
    if username in data['users']:
        data['users'][username]['storage_used'] = storage_used
        save_db(db_file, data)

def get_all_users(db_file):
    """Get all users"""
    data = load_db(db_file)
    return data['users']

def create_shared_folder(db_file, folder_id, folder_name, owner, shared_with):
    """Create a shared folder"""
    data = load_db(db_file)
    
    if 'shared_folders' not in data:
        data['shared_folders'] = {}
    
    data['shared_folders'][folder_id] = {
        'name': folder_name,
        'owner': owner,
        'shared_with': shared_with,
        'created_at': datetime.now().isoformat()
    }
    
    save_db(db_file, data)

def get_shared_folder(db_file, folder_id):
    """Get shared folder info"""
    data = load_db(db_file)
    return data.get('shared_folders', {}).get(folder_id)

def get_user_shared_folders(db_file, username):
    """Get all shared folders for a user"""
    data = load_db(db_file)
    folders = []
    
    for folder_id, folder_info in data.get('shared_folders', {}).items():
        if folder_info['owner'] == username or username in folder_info['shared_with']:
            folders.append({
                'id': folder_id,
                'name': folder_info['name'],
                'owner': folder_info['owner'],
                'is_owner': folder_info['owner'] == username,
                'shared_with': folder_info['shared_with']
            })
    
    return folders

def delete_shared_folder(db_file, folder_id):
    """Delete a shared folder"""
    data = load_db(db_file)
    if folder_id in data.get('shared_folders', {}):
        del data['shared_folders'][folder_id]
        save_db(db_file, data)
        return True
    return False

def can_access_folder(db_file, username, folder_id):
    """Check if user can access folder"""
    folder = get_shared_folder(db_file, folder_id)
    if not folder:
        return False
    return folder['owner'] == username or username in folder['shared_with']
