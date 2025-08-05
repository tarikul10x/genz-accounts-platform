# Windows Installation Guide - Gen Z Accounts Trading Platform

## Prerequisites
1. **Python 3.11 or higher** (Download from https://python.org)
2. **Git** (Optional, for version control)
3. **PostgreSQL** (For production database)

## Step 1: Download and Extract
1. Extract the project zip file to your desired location
2. Open Command Prompt or PowerShell as Administrator
3. Navigate to the project directory:
   ```cmd
   cd path\to\genz-accounts-platform
   ```

## Step 2: Python Environment Setup
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r deployment_requirements.txt
```

## Step 3: Environment Configuration
Create a `.env` file in the project root directory:

```env
# Database Configuration
DATABASE_URL=sqlite:///genZ_accounts.db

# Session Security (CHANGE THIS!)
SESSION_SECRET=your-super-secret-key-here-12345-change-this

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-from-botfather
ADMIN_TELEGRAM_ID=123456789

# Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS=credentials.json
GOOGLE_SHEETS_SPREADSHEET_NAME=GenZ Accounts Database

# Admin Configuration
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=False
```

## Step 4: Telegram Bot Setup
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token to your `.env` file
5. Get your Telegram ID from @userinfobot
6. Add your Telegram ID to `ADMIN_TELEGRAM_ID` in `.env`

## Step 5: Google Sheets Setup (Optional)
1. Go to Google Cloud Console (https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Sheets API and Google Drive API
4. Create a Service Account:
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Download the JSON credentials file
   - Rename it to `credentials.json` and place in project root
5. Create a Google Sheet and share it with the service account email

## Step 6: Initialize Database
```cmd
# Make sure you're in the project directory with activated virtual environment
python main.py
```

The application will:
- Create database tables automatically
- Initialize default category rates
- Create admin account
- Start both web server and Telegram bot

## Step 7: Access the Application
1. **Web Interface**: http://localhost:5000
2. **Admin Panel**: http://localhost:5000/admin
3. **Login**: Use username `admin` and password from `.env` file

## Step 8: Configure Categories and Rates
1. Login to admin panel
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

## Step 9: Running in Production
For production use, install and use Gunicorn:

```cmd
# Install Gunicorn (if not already installed)
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app
```

## Troubleshooting

### Common Issues:

1. **"Module not found" errors**:
   ```cmd
   # Ensure virtual environment is activated
   venv\Scripts\activate
   # Reinstall dependencies
   pip install -r deployment_requirements.txt
   ```

2. **Database errors**:
   - Check if DATABASE_URL is correct
   - Ensure you have write permissions in the project directory

3. **Telegram bot not responding**:
   - Verify TELEGRAM_BOT_TOKEN is correct
   - Check if bot is started with /start command
   - Ensure your Telegram ID is correct in ADMIN_TELEGRAM_ID

4. **Google Sheets not working**:
   - Verify credentials.json file exists and is valid
   - Check if Google Sheet is shared with service account email
   - Ensure Google Sheets API is enabled

5. **Port already in use**:
   ```cmd
   # Find process using port 5000
   netstat -ano | findstr :5000
   # Kill the process (replace PID with actual process ID)
   taskkill /F /PID 1234
   ```

### Performance Optimization:
- Use PostgreSQL for production instead of SQLite
- Configure Windows Firewall to allow port 5000
- Use reverse proxy (nginx) for better performance

### Security Recommendations:
- Change default SESSION_SECRET
- Use strong admin password
- Keep credentials.json secure
- Use HTTPS in production
- Regular backups of database

## Automatic Startup (Optional)
To run the application automatically on Windows startup:

1. Create a batch file `start_genz_platform.bat`:
   ```batch
   @echo off
   cd /d "C:\path\to\your\project"
   venv\Scripts\activate
   python main.py
   pause
   ```

2. Add the batch file to Windows startup folder:
   - Press `Win + R`, type `shell:startup`
   - Copy the batch file to this folder

## Support
- Check logs in the console output for errors
- Verify all environment variables are set correctly
- Test each component separately (web app, then bot)
- Use Python 3.11+ for best compatibility