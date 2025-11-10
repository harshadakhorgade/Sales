# Django Login Issues on EC2 - Complete Fix Guide

## Problem Summary
Login works locally but fails on EC2 because:
1. **Database Switch**: Local uses SQLite, production uses PostgreSQL
2. **Missing Environment Variables**: Critical settings not configured on EC2
3. **ALLOWED_HOSTS**: Not properly configured for EC2 domain
4. **CSRF Settings**: Missing trusted origins for your domain

## Solution Steps

### Step 1: Fix Environment Variables on EC2

Create or update your `.env` file on EC2 with these essential variables:

```bash
# On your EC2 instance, create/edit .env file
sudo nano /path/to/your/django/project/.env
```

Add these variables (replace with your actual values):

```env
# Basic Django Settings
DEBUG=False
SECRET_KEY=your-very-long-secret-key-here

# Database Configuration (PostgreSQL/RDS)
DB_NAME=your_database_name
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=5432

# Security Settings
ALLOWED_HOSTS=your-ec2-domain.com,your-elastic-ip,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://your-ec2-domain.com,http://your-elastic-ip

# AWS Settings (if using S3)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Email Settings (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Step 2: Create Superuser in Production Database

Since your production uses PostgreSQL, you need to create the superuser there:

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Navigate to your Django project
cd /path/to/your/django/project

# Activate virtual environment (if using one)
source venv/bin/activate

# Run migrations to ensure database is set up
python manage.py migrate

# Create superuser in production database
python manage.py createsuperuser
```

### Step 3: Fix ALLOWED_HOSTS

Update your environment variable to include your EC2 domain/IP:

```env
# Replace with your actual EC2 public DNS or Elastic IP
ALLOWED_HOSTS=ec2-xx-xx-xx-xx.compute-1.amazonaws.com,your-elastic-ip,localhost
```

### Step 4: Fix CSRF Settings

Add your domain to CSRF_TRUSTED_ORIGINS:

```env
# Include both HTTP and HTTPS versions
CSRF_TRUSTED_ORIGINS=https://ec2-xx-xx-xx-xx.compute-1.amazonaws.com,http://your-elastic-ip:8000
```

### Step 5: Restart Your Django Application

```bash
# If using systemd service
sudo systemctl restart your-django-service

# If using Gunicorn directly
pkill gunicorn
gunicorn --bind 0.0.0.0:8000 ecommerce.wsgi:application

# If using Docker
docker restart your-django-container
```

### Step 6: Test the Login

1. Access your application: `http://your-ec2-ip:8000/users/login/`
2. Use the superuser credentials you just created
3. Check Django logs for any errors:

```bash
# Check application logs
tail -f /var/log/your-django-app.log

# Or check system logs
sudo journalctl -f -u your-django-service
```

## Additional Debugging Steps

### Check Current Settings on EC2:

Create a temporary debug script on EC2:

```python
# debug_settings.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings

print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
print(f"DATABASE NAME: {settings.DATABASES['default']['NAME']}")
print(f"CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', 'Not set')}")
```

Run it:
```bash
python debug_settings.py
```

### Common Error Messages and Fixes:

1. **"Invalid HTTP_HOST header"**
   - Fix: Add your domain to ALLOWED_HOSTS

2. **"CSRF verification failed"**
   - Fix: Add your domain to CSRF_TRUSTED_ORIGINS

3. **"Database connection failed"**
   - Fix: Check DB credentials and ensure PostgreSQL is running

4. **"User does not exist"**
   - Fix: Create superuser in production database

### Security Best Practices:

1. **Never use DEBUG=True in production**
2. **Use strong SECRET_KEY (different from local)**
3. **Restrict ALLOWED_HOSTS to your actual domains**
4. **Use HTTPS in production (setup SSL certificate)**
5. **Use environment variables for sensitive data**

## Quick Checklist:

- [ ] Environment variables set on EC2
- [ ] Database credentials correct
- [ ] ALLOWED_HOSTS includes EC2 domain/IP
- [ ] CSRF_TRUSTED_ORIGINS configured
- [ ] Superuser created in production database
- [ ] Django service restarted
- [ ] Firewall allows port 8000 (or your port)
- [ ] Security groups allow HTTP/HTTPS traffic

## Need Help?

If you're still having issues, check:
1. EC2 Security Groups (allow inbound traffic on your port)
2. Django error logs
3. Database connectivity
4. Environment variable loading

The main issue is that your local SQLite database (with the superuser) is completely separate from your production PostgreSQL database on EC2.
