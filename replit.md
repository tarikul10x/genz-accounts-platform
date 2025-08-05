# Overview

This is a comprehensive account trading platform that combines a Flask web application with a Telegram bot. The system allows users to submit various types of social media accounts (Facebook, Instagram, Gmail, WhatsApp, etc.) through either a web interface or Telegram bot, with an admin control system for managing submissions, rates, and payments. The platform includes MLM (multi-level marketing) functionality for referral bonuses and features Google Sheets integration for account data management.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive design
- **Theme**: Dark theme implementation with custom CSS
- **JavaScript**: Vanilla JavaScript with modular component architecture
- **Static Assets**: CSS and JS files served from static directory
- **UI Components**: Card-based layouts with interactive dashboards for users and admins

## Backend Architecture
- **Framework**: Flask with Blueprint pattern for modular routing
- **Application Factory**: Prevents database initialization loops with proper app context management
- **Database ORM**: SQLAlchemy with declarative base model
- **Authentication**: Session-based with decorators for login/admin requirements
- **File Handling**: Secure file uploads with validation for Excel/CSV formats
- **Error Handling**: Comprehensive logging and rollback mechanisms

## Data Storage Solutions
- **Primary Database**: SQLite (configurable to PostgreSQL via DATABASE_URL)
- **Models**: User accounts, file submissions, category rates, withdrawals, MLM commissions, system settings
- **Relationships**: Proper foreign keys with cascade delete and lazy loading
- **Indexing**: Strategic indexes on frequently queried fields (username, telegram_id, created_at)

## Authentication and Authorization
- **User Management**: Username/password authentication with secure password hashing
- **Session Management**: Flask sessions with configurable secret keys
- **Role-Based Access**: Admin decorators and permission checks
- **Telegram Integration**: Dual authentication via web and Telegram bot

## External Dependencies
- **Telegram Bot API**: User interaction and file submission via Telegram
- **Google Sheets API**: Account data export and management
- **Payment Integration**: Support for multiple payment methods (Binance, bank transfer, mobile banking)
- **File Processing**: Pandas for Excel/CSV parsing and validation
- **MLM System**: Commission calculation and referral tracking

## Key Architectural Decisions

### Account Category System
- **Flexible Configuration**: Categories defined in config.py with subcategories and format specifications
- **Dynamic Rate Management**: Admin-configurable rates per category stored in database
- **Format Validation**: Each category has specific format requirements for account data

### Dual Interface Design
- **Web Application**: Full-featured dashboard for complex operations
- **Telegram Bot**: Streamlined interface for quick submissions and status checks
- **Shared Backend**: Both interfaces use the same models and business logic

### MLM Implementation
- **Referral System**: Multi-level commission structure with configurable rates
- **Commission Tracking**: Detailed records of all earnings and referral bonuses
- **Balance Management**: Integrated with main user balance system

### File Processing Workflow
- **Upload Validation**: File type and size checks before processing
- **Content Parsing**: Automatic account extraction from Excel/CSV files
- **Admin Review**: Manual approval/rejection system with feedback
- **Google Sheets Export**: Approved accounts exported to Google Sheets for distribution