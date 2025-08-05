import logging
import asyncio
import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError
from config import BOT_TOKEN, ADMIN_ID, ACCOUNT_CATEGORIES, PAYMENT_METHODS
from models import User, File, CategoryRate, SystemSetting, Withdrawal, AccountReport
from app import db, app
import pandas as pd
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.application = None
        self.user_states = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with proper error handling"""
        try:
            telegram_id = str(update.effective_user.id)
            username = update.effective_user.username or f"user_{telegram_id}"
            first_name = update.effective_user.first_name or ""
            last_name = update.effective_user.last_name or ""
            
            with app.app_context():
                user = User.query.filter_by(telegram_id=telegram_id).first()
                
                if not user:
                    # Handle referral code
                    referral_code = None
                    if context.args:
                        referral_code = context.args[0]
                        referrer = User.query.filter_by(referral_code=referral_code).first()
                        if referrer:
                            user = User(
                                username=username,
                                telegram_id=telegram_id,
                                first_name=first_name,
                                last_name=last_name,
                                referrer_id=referrer.id
                            )
                            db.session.add(user)
                            
                            # Generate unique referral code
                            import random
                            import string
                            user.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                            
                            # Add referral bonus
                            from mlm_system import process_referral_bonus
                            process_referral_bonus(referrer, user)
                            
                            db.session.commit()
                            
                            # Notify referrer
                            try:
                                await context.bot.send_message(
                                    referrer.telegram_id,
                                    f"🎉 New referral! {user.get_full_name()} joined using your code.\nYou earned 20 TK bonus!"
                                )
                            except:
                                pass
                        else:
                            user = User(
                                username=username,
                                telegram_id=telegram_id,
                                first_name=first_name,
                                last_name=last_name
                            )
                            db.session.add(user)
                            
                            import random
                            import string
                            user.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                            
                            db.session.commit()
                    else:
                        user = User(
                            username=username,
                            telegram_id=telegram_id,
                            first_name=first_name,
                            last_name=last_name
                        )
                        db.session.add(user)
                        
                        import random
                        import string
                        user.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                        
                        db.session.commit()
                    
                    welcome_msg = f"🎉 Welcome to Gen Z Accounts Submission!\n\n"
                    welcome_msg += f"👤 Name: {user.get_full_name()}\n"
                    welcome_msg += f"💰 Balance: {user.balance:.2f} TK\n"
                    welcome_msg += f"🔗 Your Referral Code: `{user.referral_code}`\n\n"
                    welcome_msg += "Share your referral code and earn 20 TK for each new user!"
                else:
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                    
                    welcome_msg = f"👋 Welcome back {user.get_full_name()}!\n\n"
                    welcome_msg += f"💰 Balance: {user.balance:.2f} TK\n"
                    welcome_msg += f"📈 Total Earned: {user.total_earned:.2f} TK\n"
                    welcome_msg += f"🔗 Your Referral Code: `{user.referral_code}`"
                
                # Create main menu
                keyboard = [
                    [InlineKeyboardButton("📤 Submit Accounts", callback_data="submit_accounts")],
                    [InlineKeyboardButton("💰 My Balance", callback_data="check_balance")],
                    [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_money")],
                    [InlineKeyboardButton("📊 My History", callback_data="my_history")],
                    [InlineKeyboardButton("🌐 Open Web App", web_app=WebAppInfo(url="https://your-domain.com"))],
                    [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
                ]
                
                if user.is_admin or telegram_id == str(ADMIN_ID):
                    keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    welcome_msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again.")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks with proper error handling"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            telegram_id = str(query.from_user.id)
            
            with app.app_context():
                user = User.query.filter_by(telegram_id=telegram_id).first()
                if not user:
                    await query.edit_message_text("❌ User not found. Please /start again.")
                    return
                
                # Route callbacks
                if data == "submit_accounts":
                    await self.show_categories(query, user)
                elif data == "check_balance":
                    await self.show_balance(query, user)
                elif data == "withdraw_money":
                    await self.show_withdraw_options(query, user)
                elif data == "my_history":
                    await self.show_user_history(query, user)
                elif data == "help":
                    await self.show_help(query)
                elif data == "admin_panel" and (user.is_admin or telegram_id == str(ADMIN_ID)):
                    await self.show_admin_panel(query, user)
                elif data.startswith("category_"):
                    category = data.replace("category_", "")
                    await self.show_subcategories(query, user, category)
                elif data.startswith("subcategory_"):
                    parts = data.replace("subcategory_", "").split("_")
                    if len(parts) >= 2:
                        category = parts[0]
                        subcategory = "_".join(parts[1:])
                        await self.start_file_submission(query, user, category, subcategory)
                elif data.startswith("withdraw_"):
                    method = data.replace("withdraw_", "")
                    await self.start_withdrawal(query, user, method)
                elif data.startswith("admin_"):
                    await self.handle_admin_action(query, user, data)
                elif data == "back_to_main":
                    await self.show_main_menu(query, user)
                elif data == "back_to_categories":
                    await self.show_categories(query, user)
                else:
                    await query.edit_message_text("❌ Unknown action.")
                    
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            try:
                await query.edit_message_text("❌ An error occurred. Please try again.")
            except:
                pass

    async def show_categories(self, query, user):
        """Show account categories"""
        try:
            with app.app_context():
                message = "📤 Choose account category:\n\n"
                
                keyboard = []
                for category_key, category_info in ACCOUNT_CATEGORIES.items():
                    category_rate = CategoryRate.query.filter_by(category=category_key).first()
                    if category_rate and not category_rate.is_active:
                        status = "❌ (Temporarily Disabled)"
                    else:
                        rate = category_rate.rate if category_rate else category_info['default_rate']
                        status = f"💰 {rate} TK/account"
                    
                    button_text = f"{category_info['name']} - {status}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"category_{category_key}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error showing categories: {e}")

    async def show_subcategories(self, query, user, category):
        """Show subcategories for selected category"""
        try:
            with app.app_context():
                category_rate = CategoryRate.query.filter_by(category=category).first()
                if category_rate and not category_rate.is_active:
                    await query.edit_message_text(
                        f"❌ {ACCOUNT_CATEGORIES[category]['name']} is temporarily disabled.\n\nIt will be enabled soon.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_categories")]
                        ])
                    )
                    return
                
                category_info = ACCOUNT_CATEGORIES[category]
                message = f"📤 {category_info['name']} - Choose subcategory:\n\n"
                
                keyboard = []
                for subcat_key, subcat_info in category_info['subcategories'].items():
                    rate = category_rate.rate if category_rate else category_info['default_rate']
                    button_text = f"{subcat_info['name']} - {rate} TK/account"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"subcategory_{category}_{subcat_key}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_categories")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error showing subcategories: {e}")

    async def start_file_submission(self, query, user, category, subcategory):
        """Start file submission process"""
        try:
            category_info = ACCOUNT_CATEGORIES[category]
            subcat_info = category_info['subcategories'][subcategory]
            
            self.user_states[user.telegram_id] = {
                'action': 'file_submission',
                'category': category,
                'subcategory': subcategory,
                'step': 'waiting_file'
            }
            
            message = f"📤 Submit {category_info['name']} - {subcat_info['name']}\n\n"
            message += f"📋 Required Format:\n`{subcat_info['format']}`\n\n"
            message += "📎 Please send your Excel/CSV file with accounts in the above format.\n\n"
            message += "⚠️ Make sure your file contains valid accounts in the correct format."
            
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back_to_categories")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error starting file submission: {e}")

    async def handle_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads with proper error handling"""
        try:
            telegram_id = str(update.effective_user.id)
            
            with app.app_context():
                user = User.query.filter_by(telegram_id=telegram_id).first()
                
                if not user or telegram_id not in self.user_states:
                    await update.message.reply_text("❌ Please start by choosing a category first.")
                    return
                
                user_state = self.user_states[telegram_id]
                if user_state.get('action') != 'file_submission' or user_state.get('step') != 'waiting_file':
                    await update.message.reply_text("❌ Please start by choosing a category first.")
                    return
                
                file = update.message.document
                if not file:
                    await update.message.reply_text("❌ Please send a valid file.")
                    return
                
                # Validate file
                if file.file_size > 10 * 1024 * 1024:
                    await update.message.reply_text("❌ File too large. Maximum size is 10MB.")
                    return
                
                filename = file.file_name.lower()
                if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.csv', '.txt']):
                    await update.message.reply_text("❌ Invalid file format. Please send Excel, CSV, or TXT file.")
                    return
                
                # Download and process file
                file_obj = await context.bot.get_file(file.file_id)
                file_content = await file_obj.download_as_bytearray()
                
                try:
                    if filename.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(io.BytesIO(file_content))
                    elif filename.endswith('.csv'):
                        df = pd.read_csv(io.BytesIO(file_content))
                    else:
                        content = file_content.decode('utf-8')
                        lines = content.strip().split('\n')
                        df = pd.DataFrame([line.split('\t') if '\t' in line else line.split(',') for line in lines])
                    
                    account_count = len(df)
                    
                    if account_count == 0:
                        await update.message.reply_text("❌ File is empty or invalid format.")
                        return
                    
                    if account_count > 10000:
                        await update.message.reply_text("❌ Too many accounts. Maximum 10,000 accounts per file.")
                        return
                    
                except Exception as e:
                    logger.error(f"Error parsing file: {e}")
                    await update.message.reply_text("❌ Error reading file. Please check the format and try again.")
                    return
                
                # Generate file counter
                latest_file = File.query.order_by(File.file_counter.desc()).first()
                file_counter = (latest_file.file_counter + 1) if latest_file else 1
                
                # Save file record
                file_record = File(
                    user_id=user.id,
                    filename=file.file_name,
                    category=user_state['category'],
                    subcategory=user_state['subcategory'],
                    file_format=filename.split('.')[-1],
                    file_size=file.file_size,
                    file_content=df.to_json(),
                    file_counter=file_counter,
                    account_count=account_count,
                    submission_method='bot'
                )
                
                db.session.add(file_record)
                db.session.commit()
                
                del self.user_states[telegram_id]
                
                category_info = ACCOUNT_CATEGORIES[user_state['category']]
                message = f"✅ File submitted successfully!\n\n"
                message += f"📁 File: {file.file_name}\n"
                message += f"📂 Category: {category_info['name']}\n"
                message += f"🔢 Accounts: {account_count}\n"
                message += f"🆔 Submission ID: #{file_counter}\n\n"
                message += "⏳ Your file is now pending admin approval.\n"
                message += "💰 You'll earn money once approved!"
                
                keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(message, reply_markup=reply_markup)
                
                try:
                    admin_msg = f"🔔 New file submission!\n\n"
                    admin_msg += f"👤 User: {user.get_full_name()} (@{user.username})\n"
                    admin_msg += f"📁 File: {file.file_name}\n"
                    admin_msg += f"📂 Category: {category_info['name']}\n"
                    admin_msg += f"🔢 Accounts: {account_count}\n"
                    admin_msg += f"🆔 ID: #{file_counter}"
                    
                    await context.bot.send_message(ADMIN_ID, admin_msg)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            await update.message.reply_text("❌ An error occurred while processing your file.")

    async def show_balance(self, query, user):
        """Show user balance and earnings"""
        try:
            with app.app_context():
                user = User.query.get(user.id)
                
                message = f"💰 Your Balance Information\n\n"
                message += f"💵 Current Balance: {user.balance:.2f} TK\n"
                message += f"📈 Total Earned: {user.total_earned:.2f} TK\n"
                message += f"💸 Total Withdrawn: {user.total_withdrawn:.2f} TK\n"
                message += f"🎯 MLM Earnings: {user.mlm_earnings:.2f} TK\n\n"
                
                recent_files = user.files.filter_by(status='approved').order_by(File.approved_date.desc()).limit(5).all()
                if recent_files:
                    message += "📊 Recent Earnings:\n"
                    for file_record in recent_files:
                        message += f"• {file_record.filename}: {file_record.total_earning:.2f} TK\n"
                
                message += f"\n🔗 Referral Code: `{user.referral_code}`\n"
                message += f"👥 Total Referrals: {user.total_referrals}"
                
                keyboard = [
                    [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_money")],
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Error showing balance: {e}")

    async def show_withdraw_options(self, query, user):
        """Show withdrawal options"""
        try:
            with app.app_context():
                user = User.query.get(user.id)
                
                if user.balance < 500:
                    message = f"❌ Insufficient balance for withdrawal.\n\n"
                    message += f"💰 Current Balance: {user.balance:.2f} TK\n"
                    message += f"💸 Minimum Withdrawal: 500.00 TK\n\n"
                    message += f"📈 You need {500 - user.balance:.2f} TK more to withdraw."
                    
                    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(message, reply_markup=reply_markup)
                    return
                
                message = f"💸 Choose withdrawal method:\n\n"
                message += f"💰 Available Balance: {user.balance:.2f} TK\n"
                message += f"💸 Minimum Amount: 500.00 TK\n\n"
                
                keyboard = []
                for method_key, method_info in PAYMENT_METHODS.items():
                    if method_info['is_active']:
                        keyboard.append([InlineKeyboardButton(f"{method_info['name']}", callback_data=f"withdraw_{method_key}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error showing withdraw options: {e}")

    async def start_withdrawal(self, query, user, method):
        """Start withdrawal process"""
        try:
            self.user_states[user.telegram_id] = {
                'action': 'withdrawal',
                'method': method,
                'step': 'amount'
            }
            
            method_info = PAYMENT_METHODS[method]
            message = f"💸 {method_info['name']} Withdrawal\n\n"
            message += f"💰 Available Balance: {user.balance:.2f} TK\n"
            message += f"💸 Minimum Amount: 500.00 TK\n\n"
            message += "💵 Please enter withdrawal amount:"
            
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="withdraw_money")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error starting withdrawal: {e}")

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        try:
            telegram_id = str(update.effective_user.id)
            
            with app.app_context():
                user = User.query.filter_by(telegram_id=telegram_id).first()
                
                if not user or telegram_id not in self.user_states:
                    return
                
                user_state = self.user_states[telegram_id]
                text = update.message.text.strip()
                
                if user_state.get('action') == 'withdrawal':
                    await self.handle_withdrawal_input(update, user, user_state, text, context)
                
        except Exception as e:
            logger.error(f"Error handling text message: {e}")

    async def handle_withdrawal_input(self, update, user, user_state, text, context):
        """Handle withdrawal input steps"""
        try:
            with app.app_context():
                if user_state['step'] == 'amount':
                    try:
                        amount = float(text)
                        if amount < 500:
                            await update.message.reply_text("❌ Minimum withdrawal amount is 500 TK.")
                            return
                        if amount > user.balance:
                            await update.message.reply_text("❌ Insufficient balance.")
                            return
                        
                        self.user_states[user.telegram_id]['amount'] = amount
                        self.user_states[user.telegram_id]['step'] = 'details'
                        
                        method_info = PAYMENT_METHODS[user_state['method']]
                        message = f"💸 {method_info['name']} Withdrawal - {amount:.2f} TK\n\n"
                        
                        if user_state['method'] in ['bkash', 'nagad', 'rocket']:
                            message += "📱 Please enter your mobile number:"
                        elif user_state['method'] == 'binance':
                            message += "📧 Please enter your Binance email:"
                        elif user_state['method'] == 'bank':
                            message += "🏦 Please enter your bank account details (Account Number, Bank Name, Branch):"
                        
                        await update.message.reply_text(message)
                        
                    except ValueError:
                        await update.message.reply_text("❌ Please enter a valid amount.")
                        
                elif user_state['step'] == 'details':
                    withdrawal = Withdrawal(
                        user_id=user.id,
                        amount=user_state['amount'],
                        payment_method=user_state['method'],
                        payment_details=json.dumps({'details': text}),
                        status='pending'
                    )
                    
                    db.session.add(withdrawal)
                    db.session.commit()
                    
                    del self.user_states[user.telegram_id]
                    
                    message = f"✅ Withdrawal request submitted!\n\n"
                    message += f"💰 Amount: {withdrawal.amount:.2f} TK\n"
                    message += f"💳 Method: {PAYMENT_METHODS[withdrawal.payment_method]['name']}\n"
                    message += f"🆔 Request ID: #{withdrawal.id}\n\n"
                    message += "⏳ Your request is pending admin approval."
                    
                    await update.message.reply_text(message)
                    
                    try:
                        admin_msg = f"💸 New withdrawal request!\n\n"
                        admin_msg += f"👤 User: {user.get_full_name()}\n"
                        admin_msg += f"💰 Amount: {withdrawal.amount:.2f} TK\n"
                        admin_msg += f"💳 Method: {PAYMENT_METHODS[withdrawal.payment_method]['name']}\n"
                        admin_msg += f"🆔 ID: #{withdrawal.id}"
                        
                        await context.bot.send_message(ADMIN_ID, admin_msg)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Error handling withdrawal input: {e}")

    async def show_main_menu(self, query, user):
        """Show main menu"""
        try:
            with app.app_context():
                user = User.query.get(user.id)
                
                welcome_msg = f"👋 {user.get_full_name()}\n\n"
                welcome_msg += f"💰 Balance: {user.balance:.2f} TK\n"
                welcome_msg += f"📈 Total Earned: {user.total_earned:.2f} TK"
                
                keyboard = [
                    [InlineKeyboardButton("📤 Submit Accounts", callback_data="submit_accounts")],
                    [InlineKeyboardButton("💰 My Balance", callback_data="check_balance")],
                    [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_money")],
                    [InlineKeyboardButton("📊 My History", callback_data="my_history")],
                    [InlineKeyboardButton("🌐 Open Web App", web_app=WebAppInfo(url="https://your-domain.com"))],
                    [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
                ]
                
                if user.is_admin or user.telegram_id == str(ADMIN_ID):
                    keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(welcome_msg, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")

    async def show_help(self, query):
        """Show help information"""
        try:
            message = f"ℹ️ Gen Z Accounts Submission Help\n\n"
            message += f"📤 How to submit accounts:\n"
            message += f"1. Click 'Submit Accounts'\n"
            message += f"2. Choose category and subcategory\n"
            message += f"3. Send your Excel/CSV file\n"
            message += f"4. Wait for admin approval\n\n"
            message += f"💰 Withdrawal:\n"
            message += f"• Minimum: 500 TK\n"
            message += f"• Available methods: bKash, Nagad, Rocket, Binance, Bank\n\n"
            message += f"👥 Referral System:\n"
            message += f"• Earn 20 TK for each referral\n"
            message += f"• Get commission from referral earnings\n\n"
            message += f"📞 Support: @admin_support"
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing help: {e}")

    async def show_admin_panel(self, query, user):
        """Show admin panel"""
        try:
            if not (user.is_admin or user.telegram_id == str(ADMIN_ID)):
                await query.edit_message_text("❌ Access denied.")
                return
            
            with app.app_context():
                from sqlalchemy import func
                total_users = User.query.count()
                pending_files = File.query.filter_by(status='pending').count()
                pending_withdrawals = Withdrawal.query.filter_by(status='pending').count()
                
                message = f"🛠 Admin Panel\n\n"
                message += f"👥 Total Users: {total_users}\n"
                message += f"📁 Pending Files: {pending_files}\n"
                message += f"💸 Pending Withdrawals: {pending_withdrawals}\n\n"
                message += "Choose an action:"
                
                keyboard = [
                    [InlineKeyboardButton("📁 Manage Files", callback_data="admin_files")],
                    [InlineKeyboardButton("💸 Manage Withdrawals", callback_data="admin_withdrawals")],
                    [InlineKeyboardButton("⚙️ Category Settings", callback_data="admin_categories")],
                    [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error showing admin panel: {e}")

    async def show_user_history(self, query, user):
        """Show user file history"""
        try:
            with app.app_context():
                user = User.query.get(user.id)
                files = user.files.order_by(File.created_at.desc()).limit(10).all()
                
                if not files:
                    message = "📊 No file submissions yet.\n\nStart earning by submitting your first file!"
                    keyboard = [
                        [InlineKeyboardButton("📤 Submit File", callback_data="submit_accounts")],
                        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                    ]
                else:
                    message = f"📊 Your Recent Files:\n\n"
                    for file_record in files:
                        status_emoji = "⏳" if file_record.status == "pending" else ("✅" if file_record.status == "approved" else "❌")
                        earning = f" - {file_record.total_earning:.2f} TK" if file_record.status == "approved" else ""
                        message += f"{status_emoji} {file_record.filename[:20]}{'...' if len(file_record.filename) > 20 else ''}\n"
                        message += f"   {file_record.category} • {file_record.account_count} accounts{earning}\n\n"
                    
                    keyboard = [
                        [InlineKeyboardButton("📤 Submit New File", callback_data="submit_accounts")],
                        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error showing user history: {e}")

    async def handle_admin_action(self, query, user, data):
        """Handle admin actions"""
        try:
            if not (user.is_admin or user.telegram_id == str(ADMIN_ID)):
                await query.edit_message_text("❌ Access denied.")
                return
            
            # Placeholder for admin actions
            await query.edit_message_text(
                "🛠 Admin actions are available in the web interface.\n\nPlease use the web app for detailed admin functions.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]
                ])
            )
            
        except Exception as e:
            logger.error(f"Error handling admin action: {e}")

# Global bot instance
bot_instance = TelegramBot()

def start_bot():
    """Start the Telegram bot with proper error handling"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        bot_instance.application = application
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot_instance.start_command))
        application.add_handler(CallbackQueryHandler(bot_instance.button_callback))
        application.add_handler(MessageHandler(filters.Document.ALL, bot_instance.handle_file_upload))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.handle_text_message))
        
        logger.info("Starting Telegram bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    start_bot()
