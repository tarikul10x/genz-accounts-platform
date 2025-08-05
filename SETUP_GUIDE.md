# Gen Z Accounts Trading Platform - Setup Guide

## Project Overview
Complete Flask-based Telegram bot and web application for account trading business with:
- User authentication and registration
- Admin control panel
- MLM system with 5-level commission structure
- Telegram bot integration
- Google Sheets integration
- Multiple payment methods support
- Account status checking functionality

## Features Included
✅ User Registration/Login System
✅ Account File Submission (Excel/CSV/TXT)
✅ Admin Dashboard with File Approval
✅ MLM System with Referral Codes
✅ Telegram Bot with UI Buttons
✅ Google Sheets Integration
✅ Withdrawal Management
✅ Payment Methods (bKash, Nagad, Rocket, Binance, Bank)
✅ Account Status Checker
✅ Real-time Notifications
✅ Dark Theme UI with Bootstrap
✅ Mobile Responsive Design

## Windows Setup Guide

### 1. Install Python
1. Download Python 3.11+ from https://python.org
2. During installation, check "Add Python to PATH"
3. Verify installation: `python --version`

### 2. Setup Project
```bash
# Extract the project files
# Open Command Prompt or PowerShell as Administrator
cd path\to\your\project

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r deployment_requirements.txt
```

### 3. Environment Configuration
Create `.env` file in project root:
```
# Database (for local development)
DATABASE_URL=sqlite:///genZ_accounts.db

# Session Secret (change this!)
SESSION_SECRET=your-super-secret-key-here-change-this

# Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here

# Google Sheets API (create service account on Google Cloud)
GOOGLE_SHEETS_CREDENTIALS=path/to/your/credentials.json
GOOGLE_SHEETS_SPREADSHEET_NAME=GenZ Accounts Database

# Google API Credentials (for OAuth)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Admin Settings
ADMIN_TELEGRAM_ID=your-telegram-id-here
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=change-this-password
```

### 4. Database Setup
```bash
# Run the application to create database tables
python main.py
```

### 5. Run Application
```bash
# Start the application
python main.py

# Or use Gunicorn for production
gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
```

## Cloudflare Setup Guide

### 1. Prepare for Deployment
```bash
# Create a zip file with all necessary files
# Include: all .py files, templates/, static/, .env, deployment_requirements.txt
```

### 2. Cloudflare Workers Setup
1. Go to Cloudflare Dashboard
2. Select "Workers & Pages"
3. Click "Create Application"
4. Choose "Pages" tab
5. Upload your project files

### 3. Environment Variables (Cloudflare)
In Cloudflare Pages settings, add these environment variables:
```
DATABASE_URL=your-postgresql-database-url
SESSION_SECRET=your-secret-key
TELEGRAM_BOT_TOKEN=your-bot-token
GOOGLE_SHEETS_CREDENTIALS=your-credentials-json-content
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ADMIN_TELEGRAM_ID=123456789
```

### 4. Database Setup (PostgreSQL)
For production, use PostgreSQL:
1. Create PostgreSQL database (use services like Neon, Supabase, or Railway)
2. Update DATABASE_URL in environment variables
3. The app will automatically create tables on first run

## Admin Setup Guide

### 1. First Admin Account
```bash
# Run the application
python main.py

# Access: http://localhost:5000
# Register first account with username: admin
# The system will auto-promote first user to admin
```

### 2. Telegram Bot Setup
1. Create bot with @BotFather on Telegram
2. Get bot token and add to .env file
3. Get your Telegram ID (use @userinfobot)
4. Add your Telegram ID to ADMIN_TELEGRAM_ID in .env

### 3. Google Sheets Setup
1. Go to Google Cloud Console
2. Create new project or use existing
3. Enable Google Sheets API and Google Drive API
4. Create Service Account
5. Download credentials JSON file
6. Share your Google Sheet with service account email
7. Add credentials path to .env file

### 4. Configure Categories and Rates
1. Login to admin panel: http://localhost:5000/admin
2. Go to "Category Management"
3. Set rates for each account type:
   - Facebook: 5.0 TK
   - Instagram: 4.0 TK
   - Gmail: 3.0 TK
   - WhatsApp: 6.0 TK
   - Telegram: 2.0 TK
   - Twitter: 4.5 TK
   - LinkedIn: 7.0 TK
   - TikTok: 5.5 TK

### 5. MLM System Configuration
Default MLM structure (can be modified in admin panel):
- Level 1: 15% commission
- Level 2: 10% commission
- Level 3: 7% commission
- Level 4: 5% commission
- Level 5: 3% commission

### 6. Payment Methods Setup
Configure in admin panel:
- bKash
- Nagad
- Rocket
- Binance Pay
- Bank Transfer

## Security Recommendations

### 1. Change Default Credentials
- Update SESSION_SECRET to a strong random key
- Change default admin password
- Use strong database passwords

### 2. SSL/HTTPS
- Use HTTPS in production
- Cloudflare automatically provides SSL

### 3. Environment Variables
- Never commit .env files to version control
- Use different keys for development and production

### 4. Database Security
- Use PostgreSQL for production
- Enable connection encryption
- Regular backups

## Troubleshooting

### Common Issues
1. **Bot not responding**: Check TELEGRAM_BOT_TOKEN
2. **Database errors**: Verify DATABASE_URL format
3. **Google Sheets not working**: Check credentials and sharing permissions
4. **Import errors**: Ensure all dependencies installed

### Log Files
- Application logs in console
- Check browser console for JavaScript errors
- Telegram bot logs in application output

### Support
- Check all environment variables are set correctly
- Ensure all required dependencies are installed
- Verify file permissions on Linux/Mac systems
- Test locally before deploying to production

## File Structure
```
project/
├── app.py                 # Flask app factory
├── main.py               # Main entry point
├── models.py             # Database models
├── routes.py             # Web routes
├── telegram_bot.py       # Telegram bot logic
├── admin_control.py      # Admin functions
├── google_sheets.py      # Google Sheets integration
├── mlm_system.py         # MLM calculations
├── utils.py              # Utility functions
├── config.py             # Configuration
├── templates/            # HTML templates
├── static/               # CSS, JS, images
├── .env                  # Environment variables
└── deployment_requirements.txt  # Python dependencies
```

## Next Steps
1. Test all features locally
2. Configure environment variables
3. Set up Telegram bot
4. Configure Google Sheets
5. Deploy to Cloudflare
6. Test all functionality in production