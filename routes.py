from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import pandas as pd
from io import BytesIO

from app import db
from models import User, File, CategoryRate, Withdrawal, AccountReport, SystemSetting, Notice
from config import ACCOUNT_CATEGORIES, PAYMENT_METHODS, ADMIN_ID
from admin_control import admin_control
from google_sheets import sheets_manager
from mlm_system import get_user_mlm_stats, get_mlm_genealogy
from utils import require_login, require_admin

# Create blueprints
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)
user_bp = Blueprint('user', __name__)
auth_bp = Blueprint('auth', __name__)

@main_bp.route('/')
def index():
    """Main page"""
    # Get active notices
    notices = Notice.query.filter_by(is_active=True).filter(
        (Notice.expires_at.is_(None)) | (Notice.expires_at > datetime.utcnow())
    ).order_by(Notice.created_at.desc()).limit(3).all()
    
    # Get system stats for display
    stats = {
        'total_users': User.query.count(),
        'total_earnings': db.session.query(db.func.sum(User.total_earned)).scalar() or 0,
        'total_files': File.query.filter_by(status='approved').count()
    }
    
    return render_template('index.html', notices=notices, stats=stats)

@main_bp.route('/check-account', methods=['POST'])
def check_account():
    """Check account status via AJAX"""
    try:
        uid = request.json.get('uid', '').strip()
        if not uid:
            return jsonify({'error': 'UID is required'})
        
        # Check in account reports
        report = AccountReport.query.filter_by(account_uid=uid).first()
        
        if report:
            return jsonify({
                'found': True,
                'status': report.status,
                'last_checked': report.last_checked.strftime('%Y-%m-%d %H:%M'),
                'is_duplicate': report.is_duplicate,
                'category': report.category
            })
        else:
            return jsonify({
                'found': False,
                'status': 'Not Found',
                'message': 'This account was not found in our database'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)})

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.is_banned:
                flash('Your account has been banned. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin or user.telegram_id == str(ADMIN_ID)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            if session.get('is_admin'):
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        referral_code = request.form.get('referral_code', '').strip()
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Handle referral
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                user.referrer_id = referrer.id
        
        # Generate referral code
        import random
        import string
        user.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        db.session.add(user)
        db.session.commit()
        
        # Process referral bonus if applicable
        if user.referrer_id:
            from mlm_system import process_referral_bonus
            process_referral_bonus(user.referrer, user)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

# User routes
@user_bp.route('/dashboard')
@require_login
def dashboard():
    """User dashboard"""
    user = User.query.get(session['user_id'])
    
    # Get user stats
    total_files = user.files.count()
    pending_files = user.files.filter_by(status='pending').count()
    approved_files = user.files.filter_by(status='approved').count()
    
    # Get recent files
    recent_files = user.files.order_by(File.created_at.desc()).limit(5).all()
    
    # Get MLM stats
    mlm_stats = get_user_mlm_stats(user)
    
    # Get recent withdrawals
    recent_withdrawals = user.withdrawals.order_by(Withdrawal.created_at.desc()).limit(3).all()
    
    return render_template('user/dashboard.html', 
                         user=user, 
                         total_files=total_files,
                         pending_files=pending_files,
                         approved_files=approved_files,
                         recent_files=recent_files,
                         mlm_stats=mlm_stats,
                         recent_withdrawals=recent_withdrawals)

@user_bp.route('/submit', methods=['GET', 'POST'])
@require_login
def submit_file():
    """File submission page"""
    if request.method == 'POST':
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        file = request.files.get('file')
        
        if not file or not category:
            flash('Please provide all required information', 'error')
            return redirect(url_for('user.submit_file'))
        
        # Check if category is active
        category_rate = CategoryRate.query.filter_by(category=category).first()
        if category_rate and not category_rate.is_active:
            flash('This category is temporarily disabled', 'error')
            return redirect(url_for('user.submit_file'))
        
        # Validate file
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('user.submit_file'))
        
        filename = secure_filename(file.filename)
        if not filename.lower().endswith(('.xlsx', '.xls', '.csv', '.txt')):
            flash('Invalid file format. Please upload Excel, CSV, or TXT file.', 'error')
            return redirect(url_for('user.submit_file'))
        
        try:
            # Read and process file
            file_content = file.read()
            
            if filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(BytesIO(file_content))
            elif filename.lower().endswith('.csv'):
                df = pd.read_csv(BytesIO(file_content))
            else:  # txt
                content = file_content.decode('utf-8')
                lines = content.strip().split('\n')
                df = pd.DataFrame([line.split('\t') if '\t' in line else line.split(',') for line in lines])
            
            account_count = len(df)
            
            if account_count == 0:
                flash('File is empty or invalid format', 'error')
                return redirect(url_for('user.submit_file'))
            
            if account_count > 10000:
                flash('Too many accounts. Maximum 10,000 accounts per file.', 'error')
                return redirect(url_for('user.submit_file'))
            
            # Generate file counter
            latest_file = File.query.order_by(File.file_counter.desc()).first()
            file_counter = (latest_file.file_counter + 1) if latest_file else 1
            
            # Save file record
            user = User.query.get(session['user_id'])
            file_record = File(
                user_id=user.id,
                filename=filename,
                category=category,
                subcategory=subcategory,
                file_format=filename.split('.')[-1],
                file_size=len(file_content),
                file_content=df.to_json(),
                file_counter=file_counter,
                account_count=account_count,
                submission_method='webapp'
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            flash(f'File submitted successfully! Submission ID: #{file_counter}', 'success')
            return redirect(url_for('user.history'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('user.submit_file'))
    
    # Get active categories
    categories = admin_control.get_all_category_rates()
    active_categories = {k: v for k, v in categories.items() if v['is_active']}
    
    return render_template('user/submit.html', categories=active_categories)

@user_bp.route('/history')
@require_login
def history():
    """User file history"""
    user = User.query.get(session['user_id'])
    
    page = request.args.get('page', 1, type=int)
    files = user.files.order_by(File.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('user/history.html', files=files)

@user_bp.route('/withdraw', methods=['GET', 'POST'])
@require_login
def withdraw():
    """Withdrawal page"""
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        payment_method = request.form.get('payment_method')
        
        if not user.can_withdraw(amount):
            flash('Invalid withdrawal amount', 'error')
            return redirect(url_for('user.withdraw'))
        
        # Check payment method is active
        if payment_method not in PAYMENT_METHODS or not PAYMENT_METHODS[payment_method]['is_active']:
            flash('Payment method not available', 'error')
            return redirect(url_for('user.withdraw'))
        
        # Collect payment details
        payment_details = {}
        for field in PAYMENT_METHODS[payment_method]['fields']:
            payment_details[field] = request.form.get(field, '')
        
        # Create withdrawal request
        withdrawal = Withdrawal(
            user_id=user.id,
            amount=amount,
            payment_method=payment_method,
            payment_details=json.dumps(payment_details)
        )
        
        db.session.add(withdrawal)
        db.session.commit()
        
        flash('Withdrawal request submitted successfully!', 'success')
        return redirect(url_for('user.dashboard'))
    
    # Get active payment methods
    active_methods = {k: v for k, v in PAYMENT_METHODS.items() if v['is_active']}
    
    # Get recent withdrawals
    recent_withdrawals = user.withdrawals.order_by(Withdrawal.created_at.desc()).limit(10).all()
    
    return render_template('user/withdraw.html', 
                         user=user, 
                         payment_methods=active_methods,
                         recent_withdrawals=recent_withdrawals)

# Admin routes
@admin_bp.route('/dashboard')
@require_admin
def dashboard():
    """Admin dashboard"""
    stats = admin_control.get_system_stats()
    
    # Get recent activities
    recent_files = File.query.order_by(File.created_at.desc()).limit(10).all()
    recent_withdrawals = Withdrawal.query.order_by(Withdrawal.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_files=recent_files,
                         recent_withdrawals=recent_withdrawals,
                         recent_users=recent_users)

@admin_bp.route('/users')
@require_admin
def users():
    """User management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    users_pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users_pagination, search=search)

@admin_bp.route('/files')
@require_admin
def files():
    """File management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = File.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    files_pagination = query.order_by(File.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/files.html', files=files_pagination, status_filter=status_filter)

@admin_bp.route('/file/<int:file_id>/approve', methods=['POST'])
@require_admin
def approve_file(file_id):
    """Approve file"""
    approved_count = request.form.get('approved_count', type=int)
    admin_notes = request.form.get('admin_notes', '')
    
    success, message = admin_control.approve_file(file_id, approved_count, admin_notes)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.files'))

@admin_bp.route('/file/<int:file_id>/reject', methods=['POST'])
@require_admin
def reject_file(file_id):
    """Reject file"""
    admin_notes = request.form.get('admin_notes', '')
    
    success, message = admin_control.reject_file(file_id, admin_notes)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.files'))

@admin_bp.route('/categories')
@require_admin
def categories():
    """Category management"""
    categories = admin_control.get_all_category_rates()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/category/<category>/rate', methods=['POST'])
@require_admin
def update_category_rate(category):
    """Update category rate"""
    rate = request.form.get('rate', type=float)
    is_active = request.form.get('is_active') == 'on'
    
    success, message = admin_control.set_category_rate(category, rate, is_active)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.categories'))

@admin_bp.route('/withdrawals')
@require_admin
def withdrawals():
    """Withdrawal management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Withdrawal.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    withdrawals_pagination = query.order_by(Withdrawal.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/withdrawals.html', 
                         withdrawals=withdrawals_pagination, 
                         status_filter=status_filter)

@admin_bp.route('/withdrawal/<int:withdrawal_id>/approve', methods=['POST'])
@require_admin
def approve_withdrawal(withdrawal_id):
    """Approve withdrawal"""
    admin_notes = request.form.get('admin_notes', '')
    
    success, message = admin_control.approve_withdrawal(withdrawal_id, admin_notes)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.withdrawals'))

@admin_bp.route('/withdrawal/<int:withdrawal_id>/reject', methods=['POST'])
@require_admin
def reject_withdrawal(withdrawal_id):
    """Reject withdrawal"""
    admin_notes = request.form.get('admin_notes', '')
    
    success, message = admin_control.reject_withdrawal(withdrawal_id, admin_notes)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.withdrawals'))

@admin_bp.route('/reports')
@require_admin
def reports():
    """Reports page"""
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Generate reports data
    reports_data = generate_reports_data(start_date, end_date)
    
    return render_template('admin/reports.html', 
                         reports_data=reports_data,
                         start_date=start_date,
                         end_date=end_date)

def generate_reports_data(start_date, end_date):
    """Generate reports data for date range"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # File submissions
        files_in_range = File.query.filter(
            File.created_at >= start,
            File.created_at < end
        ).all()
        
        # Withdrawals
        withdrawals_in_range = Withdrawal.query.filter(
            Withdrawal.created_at >= start,
            Withdrawal.created_at < end
        ).all()
        
        # New users
        new_users = User.query.filter(
            User.created_at >= start,
            User.created_at < end
        ).count()
        
        # Calculate totals
        total_accounts = sum(f.account_count for f in files_in_range)
        total_approved_accounts = sum(f.approved_count for f in files_in_range if f.status == 'approved')
        total_earnings = sum(f.total_earning for f in files_in_range if f.status == 'approved')
        total_withdrawal_requests = sum(w.amount for w in withdrawals_in_range)
        
        return {
            'total_files': len(files_in_range),
            'total_accounts': total_accounts,
            'total_approved_accounts': total_approved_accounts,
            'total_earnings': total_earnings,
            'total_withdrawal_requests': total_withdrawal_requests,
            'new_users': new_users,
            'files': files_in_range,
            'withdrawals': withdrawals_in_range
        }
        
    except Exception as e:
        return {'error': str(e)}
