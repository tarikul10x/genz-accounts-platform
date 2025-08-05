import logging
from functools import wraps
from flask import session, redirect, url_for, flash
from app import db
from models import User, CategoryRate, SystemSetting
from config import ACCOUNT_CATEGORIES, PAYMENT_METHODS, ADMIN_ID

logger = logging.getLogger(__name__)

def require_login(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user still exists and is active
        user = User.query.get(session['user_id'])
        if not user or user.is_banned:
            session.clear()
            flash('Your account is no longer accessible.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or user.is_banned:
            session.clear()
            flash('Your account is no longer accessible.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check admin status
        if not (user.is_admin or user.telegram_id == str(ADMIN_ID)):
            flash('Admin access required.', 'error')
            return redirect(url_for('user.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def initialize_default_data():
    """Initialize default system data"""
    try:
        logger.info("Initializing default data...")
        
        # Initialize category rates
        for category_key, category_info in ACCOUNT_CATEGORIES.items():
            existing_rate = CategoryRate.query.filter_by(category=category_key).first()
            if not existing_rate:
                category_rate = CategoryRate(
                    category=category_key,
                    rate=category_info['default_rate'],
                    is_active=category_info.get('is_active', True)
                )
                db.session.add(category_rate)
                logger.info(f"Created default rate for {category_key}: {category_info['default_rate']}")
        
        # Initialize payment method settings
        for method_key, method_info in PAYMENT_METHODS.items():
            setting_key = f'payment_{method_key}_active'
            existing_setting = SystemSetting.query.filter_by(key=setting_key).first()
            if not existing_setting:
                SystemSetting.set_value(
                    setting_key, 
                    method_info['is_active'], 
                    'boolean',
                    f'Enable/disable {method_info["name"]} payment method'
                )
                logger.info(f"Initialized payment method setting: {method_key}")
        
        # Initialize system settings
        default_settings = {
            'app_name': 'Gen Z Accounts Submission',
            'app_version': '1.0.0',
            'maintenance_mode': False,
            'min_withdrawal_amount': 500.0,
            'max_daily_withdrawals': 3,
            'referral_bonus': 20.0
        }
        
        for key, value in default_settings.items():
            existing = SystemSetting.query.filter_by(key=key).first()
            if not existing:
                data_type = 'boolean' if isinstance(value, bool) else ('float' if isinstance(value, float) else 'string')
                SystemSetting.set_value(key, value, data_type, f'System setting for {key}')
        
        # Create admin user if doesn't exist
        admin_user = User.query.filter_by(telegram_id=str(ADMIN_ID)).first()
        if not admin_user:
            admin_user = User(
                username='admin',
                telegram_id=str(ADMIN_ID),
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True
            )
            admin_user.set_password('admin123')  # Change this in production
            
            # Generate referral code
            import random
            import string
            admin_user.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            db.session.add(admin_user)
            logger.info("Created admin user")
        
        db.session.commit()
        logger.info("Default data initialization completed successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to initialize default data: {e}")

def format_currency(amount):
    """Format currency amount"""
    return f"{amount:.2f} TK"

def get_user_display_name(user):
    """Get user display name"""
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return user.username

def validate_file_format(filename):
    """Validate file format"""
    allowed_extensions = ['.xlsx', '.xls', '.csv', '.txt']
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def calculate_pagination_info(page, total_items, per_page=20):
    """Calculate pagination information"""
    total_pages = (total_items + per_page - 1) // per_page
    start_item = (page - 1) * per_page + 1
    end_item = min(page * per_page, total_items)
    
    return {
        'page': page,
        'total_pages': total_pages,
        'total_items': total_items,
        'start_item': start_item,
        'end_item': end_item,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }

def generate_secure_filename(original_filename):
    """Generate secure filename"""
    import uuid
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    extension = get_file_extension(original_filename)
    
    return f"{timestamp}_{unique_id}.{extension}"

def log_user_activity(user_id, activity, details=None):
    """Log user activity"""
    try:
        logger.info(f"User {user_id} - {activity}" + (f": {details}" if details else ""))
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def truncate_text(text, max_length=50):
    """Truncate text with ellipsis"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text

def get_status_badge_class(status):
    """Get Bootstrap badge class for status"""
    status_classes = {
        'pending': 'bg-warning',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
        'completed': 'bg-success',
        'active': 'bg-success',
        'inactive': 'bg-secondary',
        'banned': 'bg-danger',
        'unknown': 'bg-secondary',
        'ok': 'bg-success',
        'suspended': 'bg-warning',
        'wrong_password': 'bg-danger',
        'not_found': 'bg-secondary'
    }
    return status_classes.get(status.lower(), 'bg-secondary')
