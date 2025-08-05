import logging
from datetime import datetime, timedelta
from models import User, CategoryRate, SystemSetting, Notice, File, Withdrawal, AccountReport
from app import db
from config import ACCOUNT_CATEGORIES, PAYMENT_METHODS
import json

logger = logging.getLogger(__name__)

class AdminControlSystem:
    """Comprehensive admin control system for managing all aspects of the application"""
    
    def __init__(self):
        self.logger = logger
    
    def set_category_rate(self, category, rate, is_active=True):
        """Set or update category rate"""
        try:
            category_rate = CategoryRate.query.filter_by(category=category).first()
            if not category_rate:
                category_rate = CategoryRate(category=category)
                db.session.add(category_rate)
            
            category_rate.rate = float(rate)
            category_rate.is_active = is_active
            db.session.commit()
            
            self.logger.info(f"Updated category rate: {category} = {rate} (active: {is_active})")
            return True, "Rate updated successfully"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to set category rate: {e}")
            return False, f"Error: {str(e)}"
    
    def get_all_category_rates(self):
        """Get all category rates with current status"""
        try:
            rates = {}
            for category_key, category_info in ACCOUNT_CATEGORIES.items():
                db_rate = CategoryRate.query.filter_by(category=category_key).first()
                
                if db_rate:
                    rates[category_key] = {
                        'name': category_info['name'],
                        'rate': db_rate.rate,
                        'is_active': db_rate.is_active,
                        'subcategories': category_info['subcategories'],
                        'updated': db_rate.updated_date
                    }
                else:
                    rates[category_key] = {
                        'name': category_info['name'],
                        'rate': category_info['default_rate'],
                        'is_active': category_info.get('is_active', True),
                        'subcategories': category_info['subcategories'],
                        'updated': None
                    }
            
            return rates
            
        except Exception as e:
            self.logger.error(f"Failed to get category rates: {e}")
            return {}
    
    def toggle_category_status(self, category):
        """Toggle category active/inactive status"""
        try:
            category_rate = CategoryRate.query.filter_by(category=category).first()
            if not category_rate:
                # Create with default values
                default_rate = ACCOUNT_CATEGORIES.get(category, {}).get('default_rate', 0.0)
                category_rate = CategoryRate(
                    category=category,
                    rate=default_rate,
                    is_active=False
                )
                db.session.add(category_rate)
            else:
                category_rate.is_active = not category_rate.is_active
            
            db.session.commit()
            
            status = "activated" if category_rate.is_active else "deactivated"
            self.logger.info(f"Category {category} {status}")
            return True, f"Category {status} successfully"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to toggle category status: {e}")
            return False, f"Error: {str(e)}"
    
    def approve_file(self, file_id, approved_count=None, admin_notes=None):
        """Approve user file submission"""
        try:
            file_record = File.query.get(file_id)
            if not file_record:
                return False, "File not found"
            
            if file_record.status != 'pending':
                return False, "File already processed"
            
            # Set approved count (default to total count)
            if approved_count is None:
                approved_count = file_record.account_count
            else:
                approved_count = min(int(approved_count), file_record.account_count)
            
            # Get current rate for category
            category_rate = CategoryRate.query.filter_by(category=file_record.category).first()
            if category_rate:
                rate = category_rate.rate
            else:
                rate = ACCOUNT_CATEGORIES.get(file_record.category, {}).get('default_rate', 0.0)
            
            # Update file record
            file_record.status = 'approved'
            file_record.approved_count = approved_count
            file_record.rate_per_account = rate
            file_record.total_earning = approved_count * rate
            file_record.approved_date = datetime.utcnow()
            file_record.admin_notes = admin_notes
            
            # Add earnings to user
            user = file_record.user
            earning_amount = file_record.total_earning
            
            user.balance += earning_amount
            user.total_earned += earning_amount
            
            # Process MLM commission
            from mlm_system import calculate_mlm_commission
            calculate_mlm_commission(user, earning_amount)
            
            # Upload to Google Sheets
            from google_sheets import sheets_manager
            user_info = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'telegram_id': user.telegram_id,
                'email': user.email,
                'phone': user.phone,
                'payment_method': user.payment_method,
                'payment_number': user.payment_number,
                'binance_email': user.binance_email,
                'total_earned': user.total_earned,
                'balance': user.balance,
                'created_at': user.created_at.strftime('%Y-%m-%d')
            }
            
            success, sheet_url = sheets_manager.upload_accounts(
                file_record.file_content,
                user_info,
                file_record.category,
                file_record.file_counter,
                file_record.submission_method
            )
            
            if success:
                file_record.sheet_url = sheet_url
                file_record.uploaded_to_sheet = True
            
            db.session.commit()
            
            self.logger.info(f"Approved file {file_id}: {approved_count} accounts, earned {earning_amount}")
            return True, f"File approved successfully. User earned {earning_amount:.2f} TK"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to approve file: {e}")
            return False, f"Error: {str(e)}"
    
    def reject_file(self, file_id, admin_notes=None):
        """Reject user file submission"""
        try:
            file_record = File.query.get(file_id)
            if not file_record:
                return False, "File not found"
            
            if file_record.status != 'pending':
                return False, "File already processed"
            
            file_record.status = 'rejected'
            file_record.admin_notes = admin_notes
            file_record.approved_date = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(f"Rejected file {file_id}")
            return True, "File rejected successfully"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to reject file: {e}")
            return False, f"Error: {str(e)}"
    
    def approve_withdrawal(self, withdrawal_id, admin_notes=None):
        """Approve withdrawal request"""
        try:
            withdrawal = Withdrawal.query.get(withdrawal_id)
            if not withdrawal:
                return False, "Withdrawal not found"
            
            if withdrawal.status != 'pending':
                return False, "Withdrawal already processed"
            
            user = withdrawal.user
            if user.balance < withdrawal.amount:
                return False, "Insufficient user balance"
            
            # Update withdrawal
            withdrawal.status = 'approved'
            withdrawal.admin_notes = admin_notes
            withdrawal.processed_date = datetime.utcnow()
            
            # Deduct from user balance
            user.balance -= withdrawal.amount
            user.total_withdrawn += withdrawal.amount
            
            db.session.commit()
            
            self.logger.info(f"Approved withdrawal {withdrawal_id}: {withdrawal.amount} TK")
            return True, f"Withdrawal approved successfully"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to approve withdrawal: {e}")
            return False, f"Error: {str(e)}"
    
    def reject_withdrawal(self, withdrawal_id, admin_notes=None):
        """Reject withdrawal request"""
        try:
            withdrawal = Withdrawal.query.get(withdrawal_id)
            if not withdrawal:
                return False, "Withdrawal not found"
            
            if withdrawal.status != 'pending':
                return False, "Withdrawal already processed"
            
            withdrawal.status = 'rejected'
            withdrawal.admin_notes = admin_notes
            withdrawal.processed_date = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(f"Rejected withdrawal {withdrawal_id}")
            return True, "Withdrawal rejected successfully"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to reject withdrawal: {e}")
            return False, f"Error: {str(e)}"
    
    def manage_user(self, user_id, action, **kwargs):
        """Manage user account (ban, unban, adjust balance, etc.)"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            if action == 'ban':
                user.is_banned = True
                user.is_active = False
                message = f"User {user.username} banned"
                
            elif action == 'unban':
                user.is_banned = False
                user.is_active = True
                message = f"User {user.username} unbanned"
                
            elif action == 'adjust_balance':
                amount = float(kwargs.get('amount', 0))
                operation = kwargs.get('operation', 'add')
                
                if operation == 'add':
                    user.balance += amount
                    message = f"Added {amount} to user {user.username}"
                elif operation == 'subtract':
                    user.balance = max(0, user.balance - amount)
                    message = f"Subtracted {amount} from user {user.username}"
                else:
                    user.balance = amount
                    message = f"Set balance to {amount} for user {user.username}"
                
            elif action == 'set_premium':
                user.is_premium = kwargs.get('is_premium', True)
                status = "premium" if user.is_premium else "regular"
                message = f"Set user {user.username} to {status}"
                
            elif action == 'reset_password':
                new_password = kwargs.get('password', 'newpassword123')
                user.set_password(new_password)
                message = f"Password reset for user {user.username}"
                
            else:
                return False, "Invalid action"
            
            db.session.commit()
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to manage user: {e}")
            return False, f"Error: {str(e)}"
    
    def get_system_stats(self):
        """Get comprehensive system statistics"""
        try:
            from sqlalchemy import func
            
            # User statistics
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True, is_banned=False).count()
            premium_users = User.query.filter_by(is_premium=True).count()
            
            # File statistics
            total_files = File.query.count()
            pending_files = File.query.filter_by(status='pending').count()
            approved_files = File.query.filter_by(status='approved').count()
            rejected_files = File.query.filter_by(status='rejected').count()
            
            # Financial statistics
            total_earnings = db.session.query(func.sum(User.total_earned)).scalar() or 0
            total_withdrawals = db.session.query(func.sum(User.total_withdrawn)).scalar() or 0
            pending_withdrawal_amount = db.session.query(func.sum(Withdrawal.amount)).filter_by(status='pending').scalar() or 0
            
            # Withdrawal statistics
            total_withdrawal_requests = Withdrawal.query.count()
            pending_withdrawals = Withdrawal.query.filter_by(status='pending').count()
            approved_withdrawals = Withdrawal.query.filter_by(status='approved').count()
            
            return {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'premium': premium_users,
                    'banned': User.query.filter_by(is_banned=True).count()
                },
                'files': {
                    'total': total_files,
                    'pending': pending_files,
                    'approved': approved_files,
                    'rejected': rejected_files
                },
                'financial': {
                    'total_earnings': total_earnings,
                    'total_withdrawals': total_withdrawals,
                    'pending_withdrawals': pending_withdrawal_amount,
                    'platform_balance': total_earnings - total_withdrawals
                },
                'withdrawals': {
                    'total_requests': total_withdrawal_requests,
                    'pending': pending_withdrawals,
                    'approved': approved_withdrawals,
                    'rejected': Withdrawal.query.filter_by(status='rejected').count()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def create_notice(self, title, content, notice_type='info', target_audience='all', expires_hours=None):
        """Create system notice"""
        try:
            expires_at = None
            if expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            notice = Notice(
                title=title,
                content=content,
                notice_type=notice_type,
                target_audience=target_audience,
                expires_at=expires_at
            )
            
            db.session.add(notice)
            db.session.commit()
            
            self.logger.info(f"Created notice: {title}")
            return True, notice
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to create notice: {e}")
            return False, f"Error: {str(e)}"
    
    def update_payment_methods(self, updates):
        """Update payment method availability"""
        try:
            for method, is_active in updates.items():
                if method in PAYMENT_METHODS:
                    PAYMENT_METHODS[method]['is_active'] = bool(is_active)
                    SystemSetting.set_value(f'payment_{method}_active', is_active, 'boolean')
            
            self.logger.info(f"Updated payment methods: {updates}")
            return True, "Payment methods updated successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to update payment methods: {e}")
            return False, f"Error: {str(e)}"

# Global admin instance
admin_control = AdminControlSystem()
