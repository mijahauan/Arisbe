# EG-HG Web Application Deployment Guide

## 🎯 **Deployment Overview**

This guide provides comprehensive instructions for deploying the EG-HG web application on Debian 12 Linux distribution. The application consists of a Flask backend and React frontend, designed for production deployment with proper security and performance considerations.

## 🔧 **System Requirements**

### **Debian 12 Server Requirements**
- **OS**: Debian 12 (Bookworm) or later
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Network**: Internet access for package installation
- **User**: sudo privileges for installation

### **Software Dependencies**
- **Python**: 3.11+ (included in Debian 12)
- **Node.js**: 18+ for frontend build
- **Nginx**: Reverse proxy and static file serving
- **PostgreSQL**: Production database (optional, SQLite for development)
- **Git**: Source code management

## 📦 **Installation Steps**

### **1. System Preparation**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx git curl

# Install PostgreSQL (optional for production)
sudo apt install -y postgresql postgresql-contrib

# Create application user
sudo useradd -m -s /bin/bash egapp
sudo usermod -aG www-data egapp
```

### **2. Application Setup**

```bash
# Switch to application user
sudo su - egapp

# Clone or copy application files
git clone <repository-url> eg-hg-app
# OR copy files from development environment
# scp -r /path/to/py312_fix/ egapp@server:/home/egapp/eg-hg-app/

cd eg-hg-app

# Set up backend
cd eg_web_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up frontend
cd ../eg_frontend
npm install
npm run build
```

### **3. Database Configuration (Optional)**

```bash
# For PostgreSQL production setup
sudo -u postgres createuser egapp
sudo -u postgres createdb egapp_db -O egapp
sudo -u postgres psql -c "ALTER USER egapp PASSWORD 'secure_password';"

# Update Flask configuration for PostgreSQL
# Edit eg_web_backend/src/main.py to use PostgreSQL connection string
```

### **4. Environment Configuration**

```bash
# Create environment file
cat > /home/egapp/eg-hg-app/.env << EOF
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///app.db
# For PostgreSQL: DATABASE_URL=postgresql://egapp:secure_password@localhost/egapp_db
CORS_ORIGINS=https://yourdomain.com
EOF

# Set proper permissions
chmod 600 /home/egapp/eg-hg-app/.env
```

### **5. Systemd Service Configuration**

```bash
# Create systemd service file
sudo tee /etc/systemd/system/eg-hg-backend.service << EOF
[Unit]
Description=EG-HG Flask Backend
After=network.target

[Service]
Type=simple
User=egapp
Group=www-data
WorkingDirectory=/home/egapp/eg-hg-app/eg_web_backend
Environment=PATH=/home/egapp/eg-hg-app/eg_web_backend/venv/bin
EnvironmentFile=/home/egapp/eg-hg-app/.env
ExecStart=/home/egapp/eg-hg-app/eg_web_backend/venv/bin/python src/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable eg-hg-backend
sudo systemctl start eg-hg-backend
sudo systemctl status eg-hg-backend
```

### **6. Nginx Configuration**

```bash
# Create Nginx site configuration
sudo tee /etc/nginx/sites-available/eg-hg << EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration (add your certificates)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Frontend static files
    location / {
        root /home/egapp/eg-hg-app/eg_frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (for future features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/api/eg/health;
        access_log off;
    }
}
EOF

# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/eg-hg /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### **7. SSL Certificate Setup**

```bash
# Install Certbot for Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### **8. Firewall Configuration**

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
sudo ufw status
```

## 🔒 **Security Considerations**

### **Application Security**
- **Environment Variables**: Store sensitive data in `.env` file with restricted permissions
- **Secret Key**: Generate strong, unique secret key for Flask sessions
- **CORS Configuration**: Restrict origins to your domain only
- **Input Validation**: All API endpoints include input validation
- **Error Handling**: Production mode hides detailed error messages

### **Server Security**
- **Regular Updates**: Keep system packages updated
- **Firewall**: Only allow necessary ports (22, 80, 443)
- **SSL/TLS**: Use strong encryption and modern protocols
- **User Permissions**: Run application as non-privileged user
- **Log Monitoring**: Monitor application and access logs

### **Database Security**
- **Authentication**: Use strong passwords for database users
- **Network Access**: Restrict database access to localhost only
- **Backups**: Implement regular database backups
- **Encryption**: Consider database encryption for sensitive data

## 📊 **Monitoring & Maintenance**

### **Log Management**

```bash
# Application logs
sudo journalctl -u eg-hg-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo tail -f /var/log/syslog
```

### **Performance Monitoring**

```bash
# System resources
htop
df -h
free -h

# Application health
curl https://yourdomain.com/health

# Nginx status
sudo systemctl status nginx
```

### **Backup Strategy**

```bash
# Create backup script
cat > /home/egapp/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/home/egapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p \$BACKUP_DIR

# Backup application files
tar -czf \$BACKUP_DIR/app_\$DATE.tar.gz /home/egapp/eg-hg-app

# Backup database (if using PostgreSQL)
# pg_dump egapp_db > \$BACKUP_DIR/db_\$DATE.sql

# Clean old backups (keep last 7 days)
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
EOF

chmod +x /home/egapp/backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/egapp/backup.sh") | crontab -
```

## 🚀 **Deployment Verification**

### **Health Checks**

```bash
# Test backend API
curl -X GET https://yourdomain.com/api/eg/health

# Test frontend
curl -I https://yourdomain.com/

# Test graph creation
curl -X POST https://yourdomain.com/api/eg/graphs \
  -H "Content-Type: application/json" \
  -d "{}"
```

### **Performance Testing**

```bash
# Install Apache Bench for load testing
sudo apt install -y apache2-utils

# Test API performance
ab -n 100 -c 10 https://yourdomain.com/api/eg/health

# Test frontend performance
ab -n 100 -c 10 https://yourdomain.com/
```

## 🔧 **Troubleshooting**

### **Common Issues**

1. **Service Won't Start**
   ```bash
   sudo journalctl -u eg-hg-backend --no-pager
   sudo systemctl status eg-hg-backend
   ```

2. **Nginx Configuration Errors**
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Permission Issues**
   ```bash
   sudo chown -R egapp:www-data /home/egapp/eg-hg-app
   sudo chmod -R 755 /home/egapp/eg-hg-app
   ```

4. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Test database connection
   psql -h localhost -U egapp -d egapp_db
   ```

### **Performance Optimization**

1. **Enable Gzip Compression**
   ```nginx
   # Add to Nginx configuration
   gzip on;
   gzip_vary on;
   gzip_min_length 1024;
   gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
   ```

2. **Configure Caching**
   ```nginx
   # Add cache headers for static assets
   location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

3. **Database Optimization**
   ```sql
   -- Create indexes for frequently queried fields
   CREATE INDEX idx_graph_id ON graphs(id);
   CREATE INDEX idx_context_parent ON contexts(parent_context);
   ```

## 📈 **Scaling Considerations**

### **Horizontal Scaling**
- **Load Balancer**: Use Nginx or HAProxy for multiple backend instances
- **Database Clustering**: PostgreSQL replication for read scaling
- **CDN**: CloudFlare or AWS CloudFront for static asset delivery
- **Container Deployment**: Docker and Kubernetes for orchestration

### **Vertical Scaling**
- **Memory**: Increase RAM for better caching and performance
- **CPU**: More cores for concurrent request handling
- **Storage**: SSD storage for faster database operations
- **Network**: Higher bandwidth for better user experience

## ✅ **Deployment Checklist**

- [ ] System packages updated
- [ ] Application user created
- [ ] Backend dependencies installed
- [ ] Frontend built and optimized
- [ ] Environment variables configured
- [ ] Systemd service created and running
- [ ] Nginx configured and running
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Health checks passing
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Performance tested
- [ ] Security review completed

## 🎉 **Deployment Complete**

Your EG-HG web application is now successfully deployed on Debian 12 with production-grade configuration, security, and monitoring. The application is accessible via HTTPS and ready for research, education, and practical use of Peirce's Existential Graph system.

