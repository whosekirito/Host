# Admin Access Guide - Oppai Xd

## Admin Account Setup

### Initial Admin Access
The admin account is automatically created with the following credentials:
- **Email**: whosekirito@gmail.com
- **Password**: admin123 (CHANGE THIS IMMEDIATELY!)
- **User ID**: admin
- **Plan**: Pro (unlimited access)

### First Time Setup
1. **Login to Admin Account**:
   - Go to the login page
   - Use email: `whosekirito@gmail.com`
   - Use password: `admin123`
   - Complete email verification if prompted

2. **Change Admin Password**:
   - After login, go to your profile settings
   - Change the password to something secure
   - Update the password in the database if needed

3. **Access Admin Panel**:
   - Once logged in, you'll see an "Admin" link in the navigation
   - Click on "Admin" to access the admin dashboard

## Admin Panel Features

### 1. User Management
- **View All Users**: See all registered users with their details
- **User Statistics**: Total users, free users, premium users
- **Edit User Plans**: Change any user's subscription plan
- **User Details**: View user ID, email, plan, creation date

### 2. File Management
- **View All Files**: See all files uploaded by users
- **File Statistics**: Total files, file types, sizes
- **Delete Files**: Remove files if necessary
- **File Details**: View file owner, size, upload date

### 3. Subscription Management
- **Plan Management**: View and edit subscription plans
- **Pricing Control**: Update plan prices
- **Feature Limits**: Modify file upload limits per plan
- **Plan Status**: Enable/disable plans

### 4. System Statistics
- **Dashboard Overview**: Key metrics and statistics
- **User Growth**: Track user registration trends
- **Storage Usage**: Monitor file storage consumption
- **Revenue Tracking**: View subscription revenue

## Admin Functions

### Managing User Subscriptions

1. **Upgrade User Plan**:
   - Go to Admin Panel → Users tab
   - Find the user you want to upgrade
   - Click the edit button (pencil icon)
   - Select new plan: Free, Basic, Premium, or Pro
   - Click "Update Plan"

2. **Downgrade User Plan**:
   - Same process as upgrade
   - Select a lower-tier plan
   - User will be notified of changes

3. **View User Details**:
   - Click on any user in the users table
   - View their complete profile information
   - See their file upload history

### Managing Plans and Pricing

1. **Update Plan Prices**:
   - Go to Admin Panel → Plans & Pricing tab
   - Click "Edit" on any plan
   - Update the price in Indian Rupees
   - Update maximum file limits
   - Save changes

2. **Create New Plans**:
   - Currently supports 4 plans: Free, Basic, Premium, Pro
   - To add new plans, modify the database schema
   - Update the frontend templates

### Security Features

1. **Gmail-Only Registration**:
   - Only Gmail addresses are accepted for registration
   - Email verification is required for all accounts
   - Admin can verify emails manually if needed

2. **Admin Access Control**:
   - Only users with `is_admin = true` can access admin panel
   - Admin privileges are checked on every admin action
   - Session-based authentication

## Database Schema

### Users Table
```sql
- id: Primary key
- user_id: Unique 10-character ID
- username: Display name
- email: Gmail address only
- password: Hashed password
- plan: free/basic/premium/pro
- is_verified: Email verification status
- verification_code: 6-digit verification code
- verification_expires: Code expiration time
- is_admin: Admin privileges (true/false)
- created_at: Registration timestamp
- updated_at: Last update timestamp
```

### Files Table
```sql
- id: Primary key
- user_id: Foreign key to users table
- original_name: Original filename
- stored_name: Unique stored filename
- file_size: File size in bytes
- file_type: File extension
- created_at: Upload timestamp
```

### Plans Table
```sql
- id: Primary key
- plan_name: Plan identifier
- price: Price in paise (Indian currency)
- max_files: Maximum file uploads allowed
- description: Plan description
- is_active: Plan availability
- created_at: Creation timestamp
- updated_at: Last update timestamp
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Flask Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False

# Email Configuration
GMAIL_APP_PASSWORD=your-gmail-app-password
```

## Gmail App Password Setup

To enable email verification, you need to set up a Gmail App Password:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Copy the 16-character password
3. **Set Environment Variable**:
   - Add `GMAIL_APP_PASSWORD=your-16-character-password` to `.env`

## Deployment Notes

### Netlify Functions
- The app is configured for Netlify deployment
- Functions are in `/netlify/functions/app.py`
- Database connection is handled via Supabase

### File Storage
- Files are stored in Supabase Storage
- Bucket name: `oppai-files`
- File size limit: 100MB per file
- Supported formats: txt, pdf, images, videos, documents, code files

## Troubleshooting

### Common Issues

1. **Admin Panel Not Accessible**:
   - Check if user has `is_admin = true` in database
   - Verify user is logged in
   - Check session data

2. **Email Verification Not Working**:
   - Verify Gmail App Password is correct
   - Check SMTP settings
   - Ensure email is Gmail address

3. **File Upload Issues**:
   - Check Supabase storage configuration
   - Verify file size limits
   - Check file type restrictions

4. **Database Connection Issues**:
   - Verify Supabase credentials
   - Check network connectivity
   - Review error logs

### Support
For technical support or issues:
- Email: whosekirito@gmail.com
- Check application logs for detailed error messages
- Verify all environment variables are set correctly

## Security Recommendations

1. **Change Default Admin Password** immediately
2. **Use Strong Passwords** for all accounts
3. **Enable 2FA** on Gmail account
4. **Regular Security Updates** of dependencies
5. **Monitor Admin Access** logs
6. **Backup Database** regularly
7. **Use HTTPS** in production
8. **Limit Admin Access** to trusted personnel only

---

**Important**: This admin guide contains sensitive information. Keep it secure and only share with authorized personnel.