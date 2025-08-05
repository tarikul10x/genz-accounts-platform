from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    telegram_id = Column(String(20), unique=True, nullable=True, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(256), nullable=True)
    
    # Financial fields
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    total_withdrawn = Column(Float, default=0.0)
    
    # Payment details
    payment_method = Column(String(20), nullable=True)
    payment_number = Column(String(50), nullable=True)
    binance_email = Column(String(120), nullable=True)
    bank_account = Column(String(100), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # MLM fields
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_code = Column(String(10), unique=True, nullable=True, index=True)
    total_referrals = Column(Integer, default=0)
    mlm_earnings = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships with proper foreign key specification
    referrer = relationship('User', remote_side=[id], backref='referrals', post_update=True)
    files = relationship('File', foreign_keys='File.user_id', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    withdrawals = relationship('Withdrawal', foreign_keys='Withdrawal.user_id', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    account_reports = relationship('AccountReport', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def can_withdraw(self, amount):
        """Check if user can withdraw amount"""
        return self.balance >= amount and amount >= 500
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'telegram_id': self.telegram_id,
            'full_name': self.get_full_name(),
            'email': self.email,
            'phone': self.phone,
            'balance': self.balance,
            'total_earned': self.total_earned,
            'is_active': self.is_active,
            'is_banned': self.is_banned,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CategoryRate(db.Model):
    __tablename__ = 'category_rates'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(50), unique=True, nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    rate = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True, index=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (Index('idx_category_subcategory', 'category', 'subcategory'),)

class File(db.Model):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # File details
    filename = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    file_format = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_content = Column(Text, nullable=True)
    file_counter = Column(Integer, nullable=False, unique=True, index=True)
    
    # Account details
    account_count = Column(Integer, nullable=False)
    approved_count = Column(Integer, default=0)
    rate_per_account = Column(Float, default=0.0)
    total_earning = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default='pending', index=True)
    submission_method = Column(String(10), default='bot')
    
    # Admin fields
    admin_notes = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Google Sheets
    sheet_url = Column(String(500), nullable=True)
    uploaded_to_sheet = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    approved_date = Column(DateTime, nullable=True)
    
    # Admin relationship (separate from user relationship)
    admin_user = relationship('User', foreign_keys=[approved_by])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'category': self.category,
            'subcategory': self.subcategory,
            'account_count': self.account_count,
            'approved_count': self.approved_count,
            'total_earning': self.total_earning,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.username if hasattr(self, 'user') and self.user else None
        }

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Withdrawal details
    amount = Column(Float, nullable=False)
    payment_method = Column(String(20), nullable=False)
    payment_details = Column(Text, nullable=False)
    
    # Status
    status = Column(String(20), default='pending', index=True)
    admin_notes = Column(Text, nullable=True)
    processed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_date = Column(DateTime, nullable=True)
    
    # Admin relationship (separate from user relationship)
    admin_user = relationship('User', foreign_keys=[processed_by])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.username if hasattr(self, 'user') and self.user else None
        }

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    data_type = Column(String(20), default='string')
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_value(key, default=None):
        """Get system setting value"""
        try:
            setting = SystemSetting.query.filter_by(key=key).first()
            if not setting:
                return default
                
            if setting.data_type == 'integer':
                return int(setting.value)
            elif setting.data_type == 'float':
                return float(setting.value)
            elif setting.data_type == 'boolean':
                return setting.value.lower() in ('true', '1', 'yes', 'on')
            elif setting.data_type == 'json':
                import json
                return json.loads(setting.value)
            else:
                return setting.value
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def set_value(key, value, data_type='string', description=None):
        """Set system setting value"""
        from app import db
        setting = SystemSetting.query.filter_by(key=key).first()
        
        if not setting:
            setting = SystemSetting(
                key=key,
                value=str(value) if data_type != 'json' else value,
                data_type=data_type,
                description=description
            )
            db.session.add(setting)
        else:
            if data_type == 'json':
                import json
                setting.value = json.dumps(value)
            else:
                setting.value = str(value)
                
            setting.data_type = data_type
            if description:
                setting.description = description
                
        db.session.commit()
        return setting

class Notice(db.Model):
    __tablename__ = 'notices'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    notice_type = Column(String(20), default='info')
    target_audience = Column(String(20), default='all')
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

class AccountReport(db.Model):
    __tablename__ = 'account_reports'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Account details
    account_uid = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    status = Column(String(20), default='unknown', index=True)
    
    # Report details
    report_date = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow)
    check_count = Column(Integer, default=1)
    
    # Admin fields
    is_duplicate = Column(Boolean, default=False, index=True)
    admin_status = Column(String(20), nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    __table_args__ = (Index('idx_account_uid', 'account_uid'),)

class MLMCommission(db.Model):
    __tablename__ = 'mlm_commissions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    source_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    commission_type = Column(String(20), nullable=False)
    commission_amount = Column(Float, nullable=False)
    source_amount = Column(Float, nullable=False)
    commission_rate = Column(Float, nullable=False)
    
    # References
    file_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    source_user = relationship('User', foreign_keys=[source_user_id])
    file = relationship('File')
