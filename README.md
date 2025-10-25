# Oppai Xd - File Hosting Platform

A modern, secure file hosting platform built with Flask and designed for Netlify deployment.

## Features

- 🚀 **Modern UI**: Beautiful, responsive design with Bootstrap 5
- 🔒 **Secure**: Enterprise-grade security and encryption
- ⚡ **Fast**: Optimized for speed and performance
- 📱 **Mobile Friendly**: Responsive design that works on all devices
- ☁️ **Cloud Storage**: Powered by Supabase for reliable storage
- 💰 **Flexible Pricing**: Free and premium plans available

## Project Structure

```
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── index.html            # Static homepage (for Netlify)
├── netlify.toml          # Netlify deployment configuration
├── requirements.txt      # Python dependencies
├── templates/            # Flask templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── plans.html
│   └── admin.html
└── netlify/
    └── functions/
        ├── app.py        # Netlify serverless function
        └── requirements.txt
```

## Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file with:
   ```
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-key
   SUPABASE_SERVICE_KEY=your-supabase-service-key
   SECRET_KEY=your-secret-key-here
   DEBUG=true
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the website**:
   Open http://localhost:5000 in your browser

## Netlify Deployment

### Option 1: Static Site (Recommended)

The project includes a static `index.html` file that can be deployed directly to Netlify:

1. **Connect your repository** to Netlify
2. **Set build settings**:
   - Build command: `echo 'Static site build complete'`
   - Publish directory: `.`
3. **Deploy** - Netlify will automatically deploy your site

### Option 2: Serverless Functions

For full Flask functionality with serverless functions:

1. **Connect your repository** to Netlify
2. **Set build settings**:
   - Build command: `pip install -r netlify/functions/requirements.txt`
   - Publish directory: `.`
3. **Set environment variables** in Netlify dashboard
4. **Deploy** - The Flask app will run as serverless functions

## Environment Variables

Required environment variables for full functionality:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key
- `SECRET_KEY`: Flask secret key for sessions

## Database Setup

1. Create a Supabase project
2. Run the SQL schema from `database_schema.sql`
3. Set up the storage bucket for file uploads
4. Configure the environment variables

## Features Overview

### Homepage
- Modern hero section with call-to-action
- Feature showcase with icons and descriptions
- Pricing plans comparison
- Responsive design for all devices

### User Authentication
- User registration and login
- Session management
- Password hashing with Werkzeug

### File Management
- File upload with drag & drop
- File type validation
- File download and deletion
- Storage quota management

### Admin Panel
- User management
- File statistics
- Plan management

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage
- **Deployment**: Netlify
- **Icons**: Font Awesome

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team.
