# 🚀 Production Quick Start

Get your cloud storage live on the internet in minutes!

---

## 📦 What's Changed

### New Structure (Production-Ready)
```
cloud-storage/
├── config.py              # Configuration management
├── app_production.py      # Main application (factory pattern)
├── database.py            # Database operations
├── utils.py               # Utility functions
├── routes.py              # All URL endpoints
├── wsgi.py                # WSGI entry point
├── requirements.txt       # Python dependencies
├── .env.example           # Configuration template
├── gunicorn_config.py     # Production server config
├── Dockerfile             # Docker container
├── docker-compose.yml     # Docker orchestration
├── cloud-storage.service  # Systemd service
├── nginx_config.conf      # Nginx reverse proxy
└── storage_templates/     # HTML templates
└── storage_static/        # CSS/JS files
```

### Old vs New

| Old (Local) | New (Production) |
|-------------|------------------|
| Single file | Modular structure |
| Hardcoded config | Environment variables |
| Flask dev server | Gunicorn + Nginx |
| Local only | Internet accessible |
| No SSL | HTTPS ready |
| No logging | Production logging |

---

## ⚡ Super Quick Deploy (3 Options)

### Option 1: Docker (Easiest)

```bash
# 1. Extract files
tar -xzf cloud-storage-production.tar.gz
cd cloud-storage

# 2. Configure
cp .env.example .env
nano .env  # Set SECRET_KEY

# 3. Run
docker-compose up -d

# Done! Access at http://localhost:5000
```

### Option 2: VPS (Most Common)

```bash
# 1. Upload to server
scp cloud-storage-production.tar.gz user@your-server:~

# 2. SSH to server
ssh user@your-server

# 3. Extract
tar -xzf cloud-storage-production.tar.gz
cd cloud-storage

# 4. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure
cp .env.example .env
nano .env  # Set SECRET_KEY and settings

# 6. Run
gunicorn --config gunicorn_config.py wsgi:app

# Access at http://your-server-ip:5000
```

### Option 3: Platform-as-a-Service

**Railway.app / Render.com:**
1. Push to GitHub
2. Connect repository
3. Set environment variables
4. Deploy automatically

---

## 🔑 Essential Configuration

### 1. Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy output to `.env` file:
```bash
SECRET_KEY=your-generated-key-here
```

### 2. Configure .env File

Minimum required:
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-from-above
HOST=0.0.0.0
PORT=5000
DEBUG=False
```

Optional customization:
```bash
STORAGE_LIMIT_GB=10
MAX_USERS=10
SESSION_LIFETIME_HOURS=1
```

### 3. Create Required Directories

```bash
mkdir -p user_storage shared_storage logs
chmod 755 user_storage shared_storage logs
```

---

## 🌐 Make It Public

### With Domain Name

1. **Get a domain** (Namecheap, Google Domains)
2. **Point DNS** to your server IP
3. **Setup SSL** with Let's Encrypt:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```
4. **Access**: https://yourdomain.com

### Without Domain (IP Only)

1. **Find your server IP**:
   ```bash
   curl ifconfig.me
   ```
2. **Access**: http://YOUR_IP:5000
3. **Note**: No HTTPS without domain

---

## 📋 Deployment Checklist

Before going live:

- [ ] SECRET_KEY is set to random value
- [ ] DEBUG=False in .env
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] SSL certificate installed
- [ ] Backups configured
- [ ] Logs directory writable
- [ ] Storage directories writable
- [ ] Test file upload
- [ ] Test user registration
- [ ] Domain DNS configured

---

## 🔒 Security (Critical!)

### Must Do:
1. **Change SECRET_KEY** - Never use default!
2. **Enable HTTPS** - Use Let's Encrypt (free)
3. **Firewall** - Only allow ports 80, 443, 22
4. **Updates** - Keep system updated
5. **Backups** - Daily backups of user_storage and users.json

### Nice to Have:
- Rate limiting
- Fail2ban for SSH
- Regular security audits
- Monitoring/alerting

---

## 🎯 Quick Commands

### Start Application
```bash
# Development
python3 app_production.py

# Production (Gunicorn)
gunicorn --config gunicorn_config.py wsgi:app

# With systemd
sudo systemctl start cloud-storage

# With Docker
docker-compose up -d
```

### Stop Application
```bash
# Ctrl+C (if running in terminal)

# Systemd
sudo systemctl stop cloud-storage

# Docker
docker-compose down
```

### View Logs
```bash
# Application logs
tail -f logs/cloud_storage.log

# Gunicorn logs
tail -f logs/access.log
tail -f logs/error.log

# Systemd
sudo journalctl -u cloud-storage -f

# Docker
docker-compose logs -f
```

### Restart
```bash
# Systemd
sudo systemctl restart cloud-storage

# Docker
docker-compose restart
```

---

## 🐛 Troubleshooting

### Can't access from internet

**Problem**: Works on server, not from internet
**Solution**:
1. Check firewall: `sudo ufw status`
2. Check if port is open: `sudo netstat -tlnp | grep 5000`
3. Check server IP is correct
4. Verify DNS if using domain

### 502 Bad Gateway

**Problem**: Nginx can't reach application
**Solution**:
1. Check app is running: `sudo systemctl status cloud-storage`
2. Check port matches Nginx config
3. Check logs: `sudo journalctl -u cloud-storage -n 50`

### Permission Denied

**Problem**: Can't write files
**Solution**:
```bash
sudo chown -R www-data:www-data user_storage shared_storage
sudo chmod -R 755 user_storage shared_storage
```

### Import Errors

**Problem**: Module not found
**Solution**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Monitoring

### Check if Running
```bash
# Using curl
curl http://localhost:5000

# Check process
ps aux | grep gunicorn

# Check port
sudo netstat -tlnp | grep 5000
```

### Monitor Resources
```bash
# CPU and Memory
htop

# Disk usage
df -h
du -sh user_storage/*

# Network
sudo iftop
```

---

## 🔄 Updates

### Update Application
```bash
# Stop service
sudo systemctl stop cloud-storage

# Pull updates (if using git)
git pull

# Or upload new files
scp new_files/* user@server:/var/www/cloud-storage/

# Restart
sudo systemctl start cloud-storage
```

### Update Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## 💾 Backups

### Manual Backup
```bash
# Backup everything
tar -czf backup-$(date +%Y%m%d).tar.gz user_storage shared_storage users.json

# Download to local machine
scp user@server:backup-*.tar.gz ./
```

### Automated Backup
Create `/var/www/cloud-storage/backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backups/cloud-$DATE.tar.gz user_storage shared_storage users.json
find /backups -name "cloud-*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * /var/www/cloud-storage/backup.sh
```

---

## 🎓 Next Steps

1. **Test thoroughly** before giving to users
2. **Setup monitoring** (UptimeRobot, Pingdom)
3. **Configure backups** daily
4. **Document** your specific setup
5. **Monitor usage** and adjust resources

---

## 📞 Need Help?

1. **Check logs first**: `tail -f logs/*.log`
2. **Read DEPLOYMENT_GUIDE.md**: Full detailed guide
3. **Test locally**: Run `python3 app_production.py`
4. **Check permissions**: `ls -la user_storage shared_storage`

---

## ✅ Success Indicators

You're ready when:
- ✅ Can access from internet
- ✅ HTTPS working (green padlock)
- ✅ Users can register
- ✅ Files upload successfully
- ✅ Files download correctly
- ✅ Shared folders work
- ✅ Automatic restart on reboot
- ✅ Backups running
- ✅ Logs are being written

---

## 🎉 You're Live!

Your cloud storage is now accessible on the internet!

**Share your URL with users and enjoy your personal cloud storage service! ☁️**

---

**Quick Access:**
- Development: http://localhost:5000
- Production: http://your-server-ip:5000
- With domain: https://yourdomain.com

**Default User Limits:**
- 10 users maximum
- 10GB storage per user
- 2GB max file size
- Unlimited shared folders
