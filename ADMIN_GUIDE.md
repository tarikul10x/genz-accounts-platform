# Admin Control Guide - Gen Z Accounts Trading Platform

## Admin Panel Access
- **URL**: http://localhost:5000/admin (or your domain/admin)
- **Login**: Use admin credentials from `.env` file
- **Default**: Username: `admin`, Password: from `DEFAULT_ADMIN_PASSWORD`

## Dashboard Overview

### Main Admin Dashboard Features:
1. **User Management** - View and manage user accounts
2. **File Management** - Approve/reject submitted files
3. **Category Management** - Set rates for account types
4. **Withdrawal Management** - Process withdrawal requests
5. **MLM System** - Monitor referral commissions
6. **System Settings** - Configure platform settings
7. **Reports & Analytics** - View platform statistics

## User Management

### View All Users:
- Navigate to "User Management"
- See user details: balance, earnings, status
- Search users by username or Telegram ID

### User Actions:
1. **Ban/Unban Users**:
   - Click on user to view details
   - Toggle "Banned" status
   - Banned users cannot submit files or withdraw

2. **Promote to Admin**:
   - Edit user profile
   - Check "Is Admin" option
   - Save changes

3. **Adjust User Balance**:
   - Edit user profile
   - Modify balance field
   - Add admin notes for record keeping

### User Information Available:
- Username and full name
- Telegram ID and contact info
- Current balance and total earnings
- Number of referrals
- Account creation date
- Last activity

## File Management (Account Submissions)

### Pending Files Review:
1. Go to "File Management"
2. Filter by "Pending" status
3. Review each submission:
   - File details (name, category, count)
   - User information
   - Uploaded date

### File Approval Process:
1. **Click "View Details"** for each file
2. **Review Account Data**:
   - Check account format
   - Verify account validity
   - Count actual working accounts

3. **Approval Actions**:
   - **Approve**: Enter approved account count
   - **Reject**: Provide rejection reason
   - **Partial Approve**: Approve subset of accounts

4. **Payment Calculation**:
   - System automatically calculates earnings
   - Based on approved count × category rate
   - MLM commissions distributed automatically

### File Status Types:
- **Pending**: Awaiting admin review
- **Approved**: Accepted and paid
- **Rejected**: Declined with reason
- **Processing**: Under review

## Category Rate Management

### Setting Account Rates:
1. Go to "Category Management"
2. View current rates for all categories
3. Edit rates by clicking "Edit" button

### Default Categories and Suggested Rates:
- **Facebook**: 5.0 TK per account
- **Instagram**: 4.0 TK per account
- **Gmail**: 3.0 TK per account
- **WhatsApp**: 6.0 TK per account
- **Telegram**: 2.0 TK per account
- **Twitter**: 4.5 TK per account
- **LinkedIn**: 7.0 TK per account
- **TikTok**: 5.5 TK per account

### Rate Management Tips:
- Adjust rates based on account quality
- Higher rates for verified accounts
- Consider market demand
- Update rates regularly

## Withdrawal Management

### Processing Withdrawals:
1. Go to "Withdrawal Management"
2. View pending withdrawal requests
3. Check user payment details

### Withdrawal Approval Process:
1. **Verify User Balance**: Ensure sufficient funds
2. **Check Payment Details**: Verify payment method info
3. **Process Payment**: External payment to user
4. **Update Status**:
   - **Approve**: Mark as completed
   - **Reject**: Provide reason for rejection

### Payment Methods Supported:
- **bKash**: Mobile banking number
- **Nagad**: Mobile banking number
- **Rocket**: Mobile banking number
- **Binance Pay**: Binance email address
- **Bank Transfer**: Bank account details

### Withdrawal Rules:
- Minimum withdrawal: 500 TK
- User must have sufficient balance
- Valid payment information required

## MLM System Management

### Commission Structure (Configurable):
- **Level 1**: 15% (Direct referral)
- **Level 2**: 10% (Second level)
- **Level 3**: 7% (Third level)
- **Level 4**: 5% (Fourth level)
- **Level 5**: 3% (Fifth level)

### MLM Monitoring:
1. View commission reports
2. Track referral trees
3. Monitor commission payments
4. Adjust commission rates

### MLM Configuration:
- Set commission percentages
- Enable/disable MLM system
- Set minimum earning for commission
- Configure payment frequency

## System Settings

### Platform Configuration:
1. **General Settings**:
   - Platform name and description
   - Contact information
   - Operating hours

2. **Financial Settings**:
   - Minimum withdrawal amount
   - Commission rates
   - Payment methods

3. **Telegram Bot Settings**:
   - Bot token configuration
   - Admin notifications
   - User interaction settings

4. **Google Sheets Settings**:
   - Spreadsheet configuration
   - Export settings
   - Auto-export options

## Reports & Analytics

### Available Reports:
1. **User Statistics**:
   - Total users registered
   - Active users
   - User growth trends

2. **Financial Reports**:
   - Total earnings distributed
   - Pending payments
   - Commission payouts

3. **File Submission Reports**:
   - Files processed per day
   - Approval rates
   - Category popularity

4. **MLM Reports**:
   - Referral statistics
   - Commission distributions
   - Top referrers

## Google Sheets Integration

### Account Export Process:
1. **Automatic Export**: Approved files auto-export
2. **Manual Export**: Export specific files
3. **Batch Export**: Export multiple files at once

### Sheet Management:
1. Configure target spreadsheet
2. Set up column mappings
3. Manage access permissions
4. Monitor export status

## Telegram Bot Management

### Bot Administration:
1. **User Commands**: Monitor bot usage
2. **Admin Notifications**: Receive alerts
3. **Bot Status**: Check bot health
4. **Command Configuration**: Modify bot responses

### Admin Bot Commands:
- `/admin_stats` - Platform statistics
- `/pending_files` - Files awaiting approval
- `/user_info <username>` - User details
- `/ban_user <username>` - Ban user account
- `/unban_user <username>` - Unban user account

## Security Management

### Security Features:
1. **Session Management**: Monitor admin sessions
2. **Access Logs**: Track admin actions
3. **Permission Control**: Role-based access
4. **Audit Trail**: Log all admin activities

### Security Best Practices:
- Change default admin password
- Use strong session secrets
- Regular security updates
- Monitor unusual activities

## Maintenance Tasks

### Daily Tasks:
- Review pending file submissions
- Process withdrawal requests
- Check system health
- Monitor user activities

### Weekly Tasks:
- Review financial reports
- Update category rates if needed
- Check Google Sheets integration
- Backup database

### Monthly Tasks:
- Analyze platform performance
- Review MLM commission structure
- Update system settings
- Security audit

## Troubleshooting

### Common Admin Issues:

1. **Cannot Access Admin Panel**:
   - Check admin credentials
   - Verify admin status in database
   - Clear browser cache

2. **File Upload Issues**:
   - Check file format support
   - Verify upload directory permissions
   - Monitor disk space

3. **Google Sheets Not Working**:
   - Verify credentials.json
   - Check sheet permissions
   - Test API connectivity

4. **Telegram Bot Issues**:
   - Verify bot token
   - Check webhook configuration
   - Monitor bot logs

### Getting Help:
- Check application logs
- Review error messages
- Test individual components
- Contact technical support

## Performance Monitoring

### Key Metrics to Monitor:
1. **Response Time**: Page load speeds
2. **Database Performance**: Query execution times
3. **User Activity**: Active user counts
4. **Error Rates**: Application errors

### Optimization Tips:
- Regular database maintenance
- Monitor server resources
- Optimize slow queries
- Cache frequently accessed data

This admin guide covers all major administrative functions. Regularly review these procedures to ensure smooth platform operation.