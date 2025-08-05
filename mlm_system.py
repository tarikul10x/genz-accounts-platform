import logging
from models import User, MLMCommission
from app import db
from config import MLM_CONFIG

logger = logging.getLogger(__name__)

def process_referral_bonus(referrer, new_user):
    """Process referral bonus when a new user joins"""
    try:
        if not referrer or not new_user:
            return False
        
        # Add referral bonus to referrer
        bonus_amount = MLM_CONFIG['referral_bonus']
        referrer.balance += bonus_amount
        referrer.mlm_earnings += bonus_amount
        referrer.total_referrals += 1
        
        # Create commission record
        commission = MLMCommission(
            user_id=referrer.id,
            source_user_id=new_user.id,
            commission_type='referral',
            commission_amount=bonus_amount,
            source_amount=0.0,  # No source earning for referral bonus
            commission_rate=100.0  # Fixed bonus
        )
        
        db.session.add(commission)
        db.session.commit()
        
        logger.info(f"Processed referral bonus: {referrer.username} earned {bonus_amount} TK for referring {new_user.username}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process referral bonus: {e}")
        return False

def calculate_mlm_commission(user, earning_amount):
    """Calculate and distribute MLM commission for user earning"""
    try:
        if not user or earning_amount <= 0:
            return
        
        current_user = user
        level = 1
        remaining_amount = earning_amount
        
        # Traverse up the referral chain
        while current_user.referrer and level <= MLM_CONFIG['max_levels']:
            referrer = current_user.referrer
            
            # Get commission rate for this level
            level_key = f'level{level}'
            commission_rate = MLM_CONFIG['commission_rates'].get(level_key, 0)
            
            if commission_rate > 0:
                # Calculate commission (as percentage of remaining amount)
                commission_amount = remaining_amount * commission_rate
                
                # Add commission to referrer
                referrer.balance += commission_amount
                referrer.mlm_earnings += commission_amount
                
                # Create commission record
                commission = MLMCommission(
                    user_id=referrer.id,
                    source_user_id=user.id,
                    commission_type=level_key,
                    commission_amount=commission_amount,
                    source_amount=earning_amount,
                    commission_rate=commission_rate * 100  # Store as percentage
                )
                
                db.session.add(commission)
                
                # Reduce remaining amount for next level
                remaining_amount -= commission_amount
                
                logger.info(f"MLM Level {level}: {referrer.username} earned {commission_amount:.2f} TK from {user.username}")
            
            # Move to next level
            current_user = referrer
            level += 1
        
        db.session.commit()
        logger.info(f"MLM commission distribution completed for {user.username}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to calculate MLM commission: {e}")

def get_user_mlm_stats(user):
    """Get MLM statistics for a user"""
    try:
        # Direct referrals
        direct_referrals = User.query.filter_by(referrer_id=user.id).count()
        
        # Total MLM earnings
        total_mlm_earnings = user.mlm_earnings
        
        # Commission breakdown by level
        commissions = MLMCommission.query.filter_by(user_id=user.id).all()
        
        level_earnings = {}
        for commission in commissions:
            level = commission.commission_type
            if level not in level_earnings:
                level_earnings[level] = 0
            level_earnings[level] += commission.commission_amount
        
        # Downline count (all levels)
        downline_count = 0
        downline_earnings = 0
        
        def count_downline(referrer_id, level=1):
            nonlocal downline_count, downline_earnings
            if level > MLM_CONFIG['max_levels']:
                return
            
            referrals = User.query.filter_by(referrer_id=referrer_id).all()
            for referral in referrals:
                downline_count += 1
                downline_earnings += referral.total_earned
                count_downline(referral.id, level + 1)
        
        count_downline(user.id)
        
        return {
            'direct_referrals': direct_referrals,
            'total_referrals': user.total_referrals,
            'total_mlm_earnings': total_mlm_earnings,
            'level_earnings': level_earnings,
            'downline_count': downline_count,
            'downline_total_earnings': downline_earnings,
            'referral_code': user.referral_code
        }
        
    except Exception as e:
        logger.error(f"Failed to get MLM stats for user {user.id}: {e}")
        return {}

def get_mlm_genealogy(user, max_depth=3):
    """Get MLM genealogy tree for a user"""
    try:
        def build_tree(user_id, depth=0):
            if depth >= max_depth:
                return None
            
            user = User.query.get(user_id)
            if not user:
                return None
            
            children = []
            referrals = User.query.filter_by(referrer_id=user_id).all()
            
            for referral in referrals:
                child = build_tree(referral.id, depth + 1)
                if child:
                    children.append(child)
            
            return {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'total_earned': user.total_earned,
                'mlm_earnings': user.mlm_earnings,
                'referral_count': len(referrals),
                'depth': depth,
                'children': children
            }
        
        return build_tree(user.id)
        
    except Exception as e:
        logger.error(f"Failed to get MLM genealogy for user {user.id}: {e}")
        return None

def calculate_team_earnings(user):
    """Calculate total earnings of user's team"""
    try:
        total_earnings = 0
        
        def sum_team_earnings(referrer_id, level=1):
            nonlocal total_earnings
            if level > MLM_CONFIG['max_levels']:
                return
            
            referrals = User.query.filter_by(referrer_id=referrer_id).all()
            for referral in referrals:
                total_earnings += referral.total_earned
                sum_team_earnings(referral.id, level + 1)
        
        sum_team_earnings(user.id)
        return total_earnings
        
    except Exception as e:
        logger.error(f"Failed to calculate team earnings for user {user.id}: {e}")
        return 0

def get_top_earners(limit=10):
    """Get top MLM earners"""
    try:
        top_earners = User.query.order_by(User.mlm_earnings.desc()).limit(limit).all()
        
        result = []
        for user in top_earners:
            result.append({
                'username': user.username,
                'full_name': user.get_full_name(),
                'mlm_earnings': user.mlm_earnings,
                'total_referrals': user.total_referrals,
                'team_earnings': calculate_team_earnings(user)
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get top earners: {e}")
        return []
