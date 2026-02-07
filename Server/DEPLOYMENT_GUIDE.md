# 🚀 Production Deployment Guide

Complete guide to deploy Cloud Storage to a public server.

---

## 📋 Prerequisites

### Server Requirements
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **RAM**: Minimum 2GB (4GB+ recommended)
- **Disk**: Minimum 100GB for user storage
- **CPU**: 2+ cores recommended
- **Domain**: Registered domain name (e.g., storage.yourdomain.com)

### Software Requirements
- Python 3.8+
- Nginx
- Supervisor or systemd
- SSL certificate (Let's Encrypt recommended)

---

## 🛠️ Deployment Methods

Choose one of the following methods:

### Method 1: VPS (DigitalOcean, Linode, AWS EC2)
### Method 2: Platform-as-a-Service (Heroku, Railway, Render)
### Method 3: Cloud Platform (Google Cloud, Azure)

---

## 📦 Method 1: VPS Deployment (Most Common)

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx supervisor

# Create application directory
sudo mkdir -p /var/www/cloud-storage
sudo chown $USER:$USER /var/www/cloud-storage
cd /var/www/cloud-storage
```

### Step 2: Upload Application Files

```bash
# Option A: Using Git
git clone https://your-repo/cloud-storage.git .

# Option B: Using SCP from local machine
# On your local machine:
scp -r /path/to/cloud-storage/* user@your-server:/var/www/cloud-storage/
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Update `.env` file:
```bash
FLASK_ENV=production
SECRET_KEY=generate-a-random-secret-key-here
HOST=0.0.0.0
PORT=5000
DEBUG=False
STORAGE_LIMIT_GB=10
MAX_USERS=10
```

**Generate secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Create Required Directories

```bash
# Create storage directories
mkdir -p user_storage shared_storage logs

# Set permissions
chmod 755 user_storage shared_storage
chmod 755 logs
```

### Step 6: Test Application

```bash
# Test run
python3 app_production.py

# Should see:
# Cloud Storage Application Starting
# Environment: production
# ...
```

Press Ctrl+C to stop.

### Step 7: Setup Gunicorn

```bash
# Test Gunicorn
gunicorn --config gunicorn_config.py app_production:app

# Should start without errors
# Press Ctrl+C to stop
```

### Step 8: Setup Systemd Service

```bash
# Copy service file
sudo cp cloud-storage.service /etc/systemd/system/

# Edit paths in service file
sudo nano /etc/systemd/system/cloud-storage.service

# Update these lines:
# WorkingDirectory=/var/www/cloud-storage
# ExecStart=/var/www/cloud-storage/venv/bin/gunicorn ...

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start cloud-storage

# Enable on boot
sudo systemctl enable cloud-storage

# Check status
sudo systemctl status cloud-storage
```

### Step 9: Configure Nginx

```bash
# Copy Nginx config
sudo cp nginx_config.conf /etc/nginx/sites-available/cloud-storage

# Edit configuration
sudo nano /etc/nginx/sites-available/cloud-storage

# Update:
# - server_name (your domain)
# - SSL certificate paths

# Enable site
sudo ln -s /etc/nginx/sites-available/cloud-storage /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# If OK, restart Nginx
sudo systemctl restart nginx
```

### Step 10: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d storage.yourdomain.com

# Follow prompts
# Certificate will auto-renew

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 11: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 🎯 Method 2: Heroku Deployment

### Step 1: Prepare Application

Create `Procfile`:
```
web: gunicorn app_production:app
```

Create `runtime.txt`:
```
python-3.11.0
```

### Step 2: Deploy

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-cloud-storage

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
heroku config:set STORAGE_LIMIT_GB=10

# Deploy
git push heroku main

# Open app
heroku open
```

**Note**: Heroku has ephemeral filesystem - files will be lost on restart!
For persistent storage, use Heroku with S3 or PostgreSQL (requires modification).

---

## 🌐 Method 3: Railway.app Deployment

### Step 1: Setup

1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Select the repository
4. Railway auto-detects Python

### Step 2: Configure

Add environment variables in Railway dashboard:
- `FLASK_ENV=production`
- `SECRET_KEY=[generate secure key]`
- `PORT=5000`
- `STORAGE_LIMIT_GB=10`

### Step 3: Deploy

Railway automatically deploys on push to main branch.

---

## 🔐 Security Checklist

### Before Going Live

- [ ] Change SECRET_KEY to random value
- [ ] Set DEBUG=False
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Set SESSION_COOKIE_SECURE=True
- [ ] Setup automatic backups
- [ ] Configure log rotation
- [ ] Setup monitoring
- [ ] Test file upload/download
- [ ] Test user registration/login
- [ ] Review file permissions

### Nginx Security Headers

Already included in nginx_config.conf:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security

---

## 📊 Monitoring & Maintenance

### Check Application Status

```bash
# Service status
sudo systemctl status cloud-storage

# View logs
sudo journalctl -u cloud-storage -f

# Application logs
tail -f logs/cloud_storage.log
tail -f logs/access.log
tail -f logs/error.log
```

### Restart Application

```bash
# Restart service
sudo systemctl restart cloud-storage

# Restart Nginx
sudo systemctl restart nginx
```

### Update Application

```bash
# Stop service
sudo systemctl stop cloud-storage

# Pull updates
cd /var/www/cloud-storage
git pull

# Activate venv
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl start cloud-storage
```

### Backup Data

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/cloud-storage"

mkdir -p $BACKUP_DIR

# Backup user files
tar -czf $BACKUP_DIR/user_storage_$DATE.tar.gz user_storage/

# Backup shared files
tar -czf $BACKUP_DIR/shared_storage_$DATE.tar.gz shared_storage/

# Backup database
cp users.json $BACKUP_DIR/users_$DATE.json

# Keep only last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.json" -mtime +30 -delete
```

Setup cron for daily backups:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /var/www/cloud-storage/backup.sh
```

---

## 🚨 Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u cloud-storage -n 50

# Check Python errors
cd /var/www/cloud-storage
source venv/bin/activate
python3 app_production.py
```

### Nginx Errors

```bash
# Test configuration
sudo nginx -t

# Check error log
sudo tail -f /var/log/nginx/error.log
```

### Can't Upload Files

```bash
# Check permissions
ls -la user_storage/
ls -la shared_storage/

# Fix permissions
sudo chown -R www-data:www-data user_storage/
sudo chown -R www-data:www-data shared_storage/
sudo chmod -R 755 user_storage/
sudo chmod -R 755 shared_storage/
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate
sudo certbot certificates
```

---

## 🎯 Performance Optimization

### 1. Enable Gzip Compression

Add to Nginx config:
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

### 2. Add Caching

For static files (already in config):
```nginx
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 3. Increase Gunicorn Workers

Edit `gunicorn_config.py`:
```python
workers = multiprocessing.cpu_count() * 2 + 1
```

### 4. Monitor Resource Usage

```bash
# Install htop
sudo apt install htop

# Monitor
htop

# Check disk usage
df -h
du -sh user_storage/*
```

---

## 💰 Cost Estimates

### VPS Hosting
- **DigitalOcean**: $6-12/month (Basic Droplet)
- **Linode**: $5-10/month (Shared CPU)
- **AWS Lightsail**: $5-10/month

### Domain
- **Namecheap**: $10-15/year
- **Google Domains**: $12/year

### SSL Certificate
- **Let's Encrypt**: FREE!

**Total**: ~$10-20/month

---

## ✅ Post-Deployment Checklist

- [ ] Application accessible via domain
- [ ] HTTPS working (green padlock)
- [ ] User registration working
- [ ] File upload working (test 10MB file)
- [ ] File download working
- [ ] Shared folders working
- [ ] Automatic backups configured
- [ ] Monitoring setup
- [ ] DNS configured correctly
- [ ] Firewall configured
- [ ] Service starts on reboot

---

## 📞 Getting Help

### Check Logs First
```bash
# Application logs
tail -f logs/cloud_storage.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u cloud-storage -f
```

### Common Issues

1. **502 Bad Gateway**: Application not running
   - Check: `sudo systemctl status cloud-storage`

2. **413 Request Entity Too Large**: File too big for Nginx
   - Fix: Increase `client_max_body_size` in Nginx config

3. **Permission Denied**: Wrong file permissions
   - Fix: `sudo chown -R www-data:www-data /var/www/cloud-storage`

---

## 🎉 Success!

Your cloud storage is now live and accessible to the world!

**Next Steps:**
1. Share the URL with users
2. Monitor usage and performance
3. Regular backups
4. Keep software updated
5. Monitor security advisories

---

**Your production URL**: https://storage.yourdomain.com

**Admin access**: Login with your registered account

**Need help?** Check the logs and troubleshooting section above.
