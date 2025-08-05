import logging
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json
from config import GOOGLE_CREDENTIALS, ACCOUNT_CATEGORIES

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Manage Google Sheets integration for account uploads"""
    
    def __init__(self):
        self.logger = logger
        self.gc = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Google Sheets client"""
        try:
            # Create credentials from config
            credentials = Credentials.from_service_account_info(
                GOOGLE_CREDENTIALS,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive']
            )
            
            self.gc = gspread.authorize(credentials)
            self.logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {e}")
            self.gc = None
    
    def create_spreadsheet(self, title):
        """Create a new spreadsheet"""
        try:
            if not self.gc:
                return None, "Google Sheets client not initialized"
            
            spreadsheet = self.gc.create(title)
            self.logger.info(f"Created spreadsheet: {title}")
            return spreadsheet, None
            
        except Exception as e:
            self.logger.error(f"Failed to create spreadsheet: {e}")
            return None, str(e)
    
    def upload_accounts(self, file_content, user_info, category, file_counter, submission_method):
        """Upload accounts to Google Sheets with proper error handling"""
        try:
            if not self.gc:
                return False, "Google Sheets client not initialized"
            
            # Parse file content
            if isinstance(file_content, str):
                df = pd.read_json(file_content)
            else:
                df = file_content
            
            # Create spreadsheet name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sheet_name = f"{category.upper()}_{file_counter}_{timestamp}"
            
            # Create spreadsheet
            spreadsheet, error = self.create_spreadsheet(sheet_name)
            if error:
                return False, error
            
            # Get the first worksheet
            worksheet = spreadsheet.sheet1
            
            # Prepare headers based on category
            category_info = ACCOUNT_CATEGORIES.get(category, {})
            headers = ['UID', 'Password', '2FA/Recovery', 'Email/Number', 'Status', 'Duplicate Check', 'Sender Details']
            
            # Set headers
            worksheet.update('A1:G1', [headers])
            
            # Prepare data
            data_rows = []
            for index, row in df.iterrows():
                # Convert row to list and pad/trim to match format
                row_data = row.tolist()
                
                # Ensure we have at least 4 columns for account data
                while len(row_data) < 4:
                    row_data.append('')
                
                # Add status column (initially Unknown)
                row_data.append('Unknown')
                
                # Add duplicate check formula
                duplicate_formula = f'=COUNTIF(A:A,A{index + 2})>1'
                row_data.append(duplicate_formula)
                
                # Add sender details
                sender_details = f"{user_info['username']} | {user_info.get('telegram_id', '')} | {submission_method}"
                row_data.append(sender_details)
                
                data_rows.append(row_data[:7])  # Limit to 7 columns
            
            # Upload data in batches to avoid API limits
            batch_size = 100
            for i in range(0, len(data_rows), batch_size):
                batch = data_rows[i:i + batch_size]
                start_row = i + 2  # +2 because of header row and 1-indexed
                end_row = start_row + len(batch) - 1
                range_name = f'A{start_row}:G{end_row}'
                worksheet.update(range_name, batch)
            
            # Add user info in a separate section
            user_section_start = len(data_rows) + 4
            user_data = [
                ['User Information'],
                ['Username', user_info.get('username', '')],
                ['Telegram ID', user_info.get('telegram_id', '')],
                ['Name', f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()],
                ['Email', user_info.get('email', '')],
                ['Phone', user_info.get('phone', '')],
                ['Payment Method', user_info.get('payment_method', '')],
                ['Payment Number', user_info.get('payment_number', '')],
                ['Total Earned', user_info.get('total_earned', 0)],
                ['Current Balance', user_info.get('balance', 0)],
                ['Member Since', user_info.get('created_at', '')],
                ['Submission Method', submission_method],
                ['Category', category_info.get('name', category)],
                ['Upload Time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            ]
            
            user_range = f'I{user_section_start}:J{user_section_start + len(user_data) - 1}'
            worksheet.update(user_range, user_data)
            
            # Format the sheet
            self.format_worksheet(worksheet, len(data_rows))
            
            # Share with admin email (make it viewable)
            try:
                spreadsheet.share('raiyanfardintowhid@gmail.com', perm_type='user', role='writer')
            except:
                pass  # Sharing might fail but upload can still succeed
            
            # Get sheet URL
            sheet_url = spreadsheet.url
            
            self.logger.info(f"Successfully uploaded {len(data_rows)} accounts to sheet: {sheet_url}")
            return True, sheet_url
            
        except Exception as e:
            self.logger.error(f"Failed to upload accounts: {e}")
            return False, str(e)
    
    def format_worksheet(self, worksheet, data_rows):
        """Format the worksheet for better readability"""
        try:
            # Format headers
            worksheet.format('A1:G1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
            })
            
            # Freeze header row
            worksheet.freeze(rows=1)
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 6)  # Columns A-G
            
            # Format duplicate check column
            if data_rows > 0:
                duplicate_range = f'F2:F{data_rows + 1}'
                worksheet.format(duplicate_range, {
                    'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                })
            
            self.logger.info("Worksheet formatted successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to format worksheet: {e}")
    
    def update_account_status(self, sheet_url, uid, status):
        """Update account status in Google Sheet"""
        try:
            if not self.gc:
                return False, "Google Sheets client not initialized"
            
            # Open spreadsheet by URL
            spreadsheet = self.gc.open_by_url(sheet_url)
            worksheet = spreadsheet.sheet1
            
            # Find the UID and update status
            all_values = worksheet.get_all_values()
            
            for i, row in enumerate(all_values):
                if len(row) > 0 and row[0] == uid:
                    # Update status in column E (index 4)
                    cell_range = f'E{i + 1}'
                    worksheet.update(cell_range, [[status]])
                    
                    self.logger.info(f"Updated status for UID {uid} to {status}")
                    return True, "Status updated successfully"
            
            return False, "UID not found in sheet"
            
        except Exception as e:
            self.logger.error(f"Failed to update account status: {e}")
            return False, str(e)
    
    def check_account_status(self, sheet_url, uid):
        """Check account status from Google Sheet"""
        try:
            if not self.gc:
                return None, "Google Sheets client not initialized"
            
            # Open spreadsheet by URL
            spreadsheet = self.gc.open_by_url(sheet_url)
            worksheet = spreadsheet.sheet1
            
            # Find the UID and get status
            all_values = worksheet.get_all_values()
            
            for row in all_values:
                if len(row) > 0 and row[0] == uid:
                    status = row[4] if len(row) > 4 else 'Unknown'
                    is_duplicate = row[5] if len(row) > 5 else False
                    
                    return {
                        'uid': uid,
                        'status': status,
                        'is_duplicate': is_duplicate,
                        'found': True
                    }, None
            
            return {'uid': uid, 'found': False}, None
            
        except Exception as e:
            self.logger.error(f"Failed to check account status: {e}")
            return None, str(e)
    
    def create_daily_report(self, report_data, date_str):
        """Create daily report spreadsheet"""
        try:
            if not self.gc:
                return False, "Google Sheets client not initialized"
            
            # Create report spreadsheet
            sheet_name = f"Daily_Report_{date_str}"
            spreadsheet, error = self.create_spreadsheet(sheet_name)
            if error:
                return False, error
            
            worksheet = spreadsheet.sheet1
            
            # Set headers
            headers = ['UID', 'Status', 'Category', 'Submitter', 'Upload Date', 'Duplicate']
            worksheet.update('A1:F1', [headers])
            
            # Format headers
            worksheet.format('A1:F1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
            })
            
            # Add data
            if report_data:
                data_rows = []
                for item in report_data:
                    row = [
                        item.get('uid', ''),
                        item.get('status', 'Unknown'),
                        item.get('category', ''),
                        item.get('submitter', ''),
                        item.get('upload_date', ''),
                        '=COUNTIF(A:A,A{})>1'.format(len(data_rows) + 2)
                    ]
                    data_rows.append(row)
                
                range_name = f'A2:F{len(data_rows) + 1}'
                worksheet.update(range_name, data_rows)
            
            # Share with admin
            try:
                spreadsheet.share('raiyanfardintowhid@gmail.com', perm_type='user', role='writer')
            except:
                pass
            
            return True, spreadsheet.url
            
        except Exception as e:
            self.logger.error(f"Failed to create daily report: {e}")
            return False, str(e)

# Global sheets manager instance
sheets_manager = GoogleSheetsManager()
