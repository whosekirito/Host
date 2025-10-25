# Deployment Guide - Oppai Xd

This guide will help you deploy the Oppai Xd file hosting platform to various hosting services.

## 🚀 Quick Deployment

### 1. Supabase Setup

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Sign up/Login and create a new project
   - Wait for the project to be ready

2. **Get API Keys**
   - Go to Settings > API
   - Copy your Project URL and API keys

3. **Create Storage Bucket**
   - Go to Storage in your Supabase dashboard
   - Create a new bucket named `oppai-files`
   - Set it to public if you want files to be publicly accessible

4. **Setup Database**
   - Go to SQL Editor in Supabase
   - Copy and paste the contents of `database_schema.sql`
   - Run the SQL to create tables

### 2. Environment Configuration

1. **Copy Environment File**
   ```bash
   cp .env.example .env
   ```

2. **Update .env with your credentials**
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-role-key
   SECRET_KEY=your-random-secret-key-here
   DEBUG=False
   ```

## 🌐 Deployment Options

### Option 1: Render (Recommended)

1. **Connect Repository**
   - Push your code to GitHub
   - Connect your GitHub repo to Render

2. **Create Web Service**
   - Choose "Web Service"
   - Select your repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python app.py`

3. **Environment Variables**
   - Add all variables from your `.env` file
   - Set `PORT` to `5000`

4. **Deploy**
   - Click "Deploy" and wait for completion

### Option 2: Heroku

1. **Install Heroku CLI**
   ```bash
   # Install Heroku CLI from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

3. **Create Procfile**
   ```bash
   echo "web: python app.py" > Procfile
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set SUPABASE_URL=your-url
   heroku config:set SUPABASE_KEY=your-key
   heroku config:set SUPABASE_SERVICE_KEY=your-service-key
   heroku config:set SECRET_KEY=your-secret-key
   ```

5. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

### Option 3: VPS/Cloud Server

1. **Server Setup**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and pip
   sudo apt install python3 python3-pip nginx -y
   
   # Install Gunicorn
   pip3 install gunicorn
   ```

2. **Deploy Application**
   ```bash
   # Clone your repository
   git clone your-repo-url
   cd oppai-xd
   
   # Install dependencies
   pip3 install -r requirements.txt
   
   # Create systemd service
   sudo nano /etc/systemd/system/oppai-xd.service
   ```

3. **Create Systemd Service**
   ```ini
   [Unit]
   Description=Oppai Xd File Hosting
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/oppai-xd
   Environment="PATH=/path/to/oppai-xd/venv/bin"
   ExecStart=/path/to/oppai-xd/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **Start Services**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable oppai-xd
   sudo systemctl start oppai-xd
   sudo systemctl restart nginx
   ```

### Option 4: Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .

   EXPOSE 5000

   CMD ["python", "app.py"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   services:
     oppai-xd:
       build: .
       ports:
         - "5000:5000"
       environment:
         - SUPABASE_URL=${SUPABASE_URL}
         - SUPABASE_KEY=${SUPABASE_KEY}
         - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
         - SECRET_KEY=${SECRET_KEY}
       volumes:
         - ./uploads:/app/uploads
   ```

3. **Deploy with Docker**
   ```bash
   docker-compose up -d
   ```

## 🔧 Post-Deployment Setup

### 1. Create Admin User

1. **Access your deployed application**
2. **Register a new account**
3. **Update database to make user admin**
   ```sql
   UPDATE users SET user_id = 'admin' WHERE email = 'your-email@example.com';
   ```

### 2. Configure Domain (Optional)

1. **Point your domain to your server**
2. **Update Nginx configuration with your domain**
3. **Set up SSL certificate with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### 3. Monitor Application

1. **Check logs**
   ```bash
   # For systemd service
   sudo journalctl -u oppai-xd -f
   
   # For Docker
   docker-compose logs -f
   ```

2. **Monitor resources**
   ```bash
   htop
   df -h
   ```

## 🛠️ Troubleshooting

### Common Issues

1. **Supabase Connection Error**
   - Check your API keys
   - Verify Supabase URL format
   - Ensure database tables are created

2. **File Upload Issues**
   - Check storage bucket permissions
   - Verify file size limits
   - Check allowed file types

3. **Admin Panel Access**
   - Ensure user_id is set to 'admin' in database
   - Check session management

4. **Performance Issues**
   - Increase worker processes
   - Add caching layer
   - Optimize database queries

### Logs and Debugging

1. **Enable Debug Mode**
   ```env
   DEBUG=True
   ```

2. **Check Application Logs**
   - Look for error messages
   - Monitor request/response times
   - Check database connection status

## 📊 Monitoring and Maintenance

### 1. Regular Backups

1. **Database Backups**
   - Use Supabase's built-in backup features
   - Export data regularly

2. **File Backups**
   - Backup uploaded files
   - Consider using cloud storage

### 2. Security Updates

1. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Monitor Security Advisories**
   - Check for Flask security updates
   - Update Supabase client library

### 3. Performance Monitoring

1. **Monitor Resource Usage**
   - CPU and memory usage
   - Disk space
   - Network bandwidth

2. **Database Performance**
   - Monitor query performance
   - Add indexes if needed
   - Optimize slow queries

## 🎉 Success!

Your Oppai Xd file hosting platform is now deployed and ready to use!

- **User Registration**: Users can create accounts with random IDs
- **File Upload**: Secure file storage with Supabase
- **Paid Plans**: Multiple pricing tiers in Indian Rupees
- **Admin Panel**: Complete management interface
- **Modern UI**: Beautiful, responsive design

For support and updates, check the main README.md file.