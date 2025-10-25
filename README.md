# Oppai Xd - File Hosting Platform

A modern, secure file hosting platform built with Flask and Supabase, featuring user authentication, paid plans, and an admin panel.

## 🌟 Features

- **Secure File Storage**: Enterprise-grade security with Supabase
- **User Authentication**: Registration and login with random user IDs
- **Paid Plans**: Multiple tiers with Indian Rupee pricing
- **Admin Panel**: Complete user and plan management
- **Modern UI**: Beautiful, responsive design with Bootstrap 5
- **File Management**: Upload, download, and delete files
- **Plan Management**: Admin can modify pricing and user plans

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or download the project
cd oppai-xd

# Run setup script
python setup.py
```

### 2. Configure Supabase

1. Go to [Supabase](https://supabase.com) and create a new project
2. Get your project URL and API keys from Settings > API
3. Create a storage bucket named `oppai-files`
4. Run the SQL from `database_schema.sql` in the SQL editor
5. Update `.env` file with your credentials:

```env
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SECRET_KEY=your-secret-key
```

### 3. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` to access the platform.

## 📋 Plans & Pricing

| Plan | Price | Files | Storage | Features |
|------|-------|-------|---------|----------|
| Free | ₹0 | 1 | 100MB | Basic features |
| Basic | ₹299 | 10 | 1GB | Email support, faster uploads |
| Premium | ₹799 | 50 | 5GB | Priority support, advanced features |
| Pro | ₹1,999 | 200 | 20GB | 24/7 support, API access |

## 🛠️ Admin Features

- **User Management**: View, edit, and delete users
- **Plan Management**: Modify user plans and pricing
- **File Management**: Monitor and manage uploaded files
- **Statistics**: View platform usage statistics

### Admin Access

To access the admin panel, set a user's `user_id` to `'admin'` in the database.

## 📁 Project Structure

```
oppai-xd/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── database_schema.sql   # Database schema
├── setup.py              # Setup script
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── plans.html
│   └── admin.html
└── static/              # Static files (CSS, JS, images)
```

## 🔧 Configuration

### Environment Variables

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key
- `SECRET_KEY`: Flask secret key for sessions
- `DEBUG`: Enable debug mode (True/False)

### File Upload Settings

- Maximum file size: 100MB
- Allowed extensions: txt, pdf, png, jpg, jpeg, gif, mp4, mp3, zip, rar, doc, docx, xls, xlsx, ppt, pptx, py, js, html, css

## 🚀 Deployment

### Using Render

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy automatically

### Using Heroku

1. Create a `Procfile`:
```
web: python app.py
```

2. Deploy using Heroku CLI:
```bash
heroku create your-app-name
git push heroku main
```

### Using VPS

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🔒 Security Features

- Password hashing with Werkzeug
- Secure file upload validation
- User authentication and authorization
- Admin-only access controls
- File type and size restrictions

## 📱 Mobile Support

The platform is fully responsive and works on all devices:
- Mobile phones
- Tablets
- Desktop computers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team

## 🔄 Updates

- Version 1.0.0: Initial release with basic file hosting
- Future updates will include payment integration, advanced analytics, and more features

---

**Oppai Xd** - Secure, fast, and reliable file hosting platform built with ❤️