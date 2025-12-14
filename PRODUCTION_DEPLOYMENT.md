# Production Deployment Guide

This guide covers deploying AI Arr Control to production environments with proper security, monitoring, and reliability configurations.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Linux/Systemd Deployment](#linuxsystemd-deployment)
6. [Reverse Proxy Setup](#reverse-proxy-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Security Review

- [ ] All API keys are stored securely (use environment variables or secrets manager)
- [ ] Database passwords are strong (20+ characters, mix of types)
- [ ] HTTPS/TLS is configured for remote access
- [ ] API is behind a reverse proxy or firewall
- [ ] Access logs are enabled
- [ ] No debug mode enabled in production
- [ ] Dependencies are up-to-date

### Infrastructure Requirements

- [ ] Python 3.11+ installed
- [ ] Database server running (PostgreSQL recommended for production)
- [ ] Sufficient disk space for logs and database (~100MB minimum)
- [ ] Network access to Radarr, Sonarr, Prowlarr services
- [ ] Stable internet connection for long-term uptime

### Operational Readiness

- [ ] Backup procedures documented
- [ ] Recovery procedures tested
- [ ] Monitoring alerts configured
- [ ] Support contact information documented
- [ ] Deployment team trained
- [ ] Rollback plan prepared

---

## Environment Setup

### Production Configuration File

Create `.env.production` with strict configuration:

```env
# APPLICATION
APP_NAME=AI Arr Control Production
DEBUG=false

# RADARR (adjust URLs to your environment)
RADARR_URL=https://radarr.internal.example.com
RADARR_API_KEY=<your-radarr-api-key-32-chars>

# SONARR
SONARR_URL=https://sonarr.internal.example.com
SONARR_API_KEY=<your-sonarr-api-key-32-chars>

# PROWLARR
PROWLARR_URL=https://prowlarr.internal.example.com
PROWLARR_API_KEY=<your-prowlarr-api-key-32-chars>

# DATABASE (PostgreSQL for production)
DATABASE_URL=postgresql+asyncpg://airrcontrol:STRONG_PASSWORD@db.internal:5432/ai_arr_control

# DISCOVERY (disable in production unless needed)
DISCOVERY_ENABLED=false

# PERFORMANCE
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
```

### Permission Setup

```bash
# Create application user
sudo useradd -r -s /bin/false airrcontrol

# Create directory with proper permissions
sudo mkdir -p /opt/ai_arr_control
sudo chown airrcontrol:airrcontrol /opt/ai_arr_control
sudo chmod 750 /opt/ai_arr_control

# Create log directory
sudo mkdir -p /var/log/ai_arr_control
sudo chown airrcontrol:airrcontrol /var/log/ai_arr_control
sudo chmod 755 /var/log/ai_arr_control

# Create data directory for database files (SQLite only)
sudo mkdir -p /var/lib/ai_arr_control
sudo chown airrcontrol:airrcontrol /var/lib/ai_arr_control
sudo chmod 750 /var/lib/ai_arr_control
```

---

## Database Configuration

### PostgreSQL Setup (Recommended)

```bash
# Install PostgreSQL client
sudo apt-get install postgresql-client

# Connect to PostgreSQL server
psql -h db.internal -U postgres

# Create database and user
CREATE DATABASE ai_arr_control;
CREATE USER airrcontrol WITH ENCRYPTED PASSWORD 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE ai_arr_control TO airrcontrol;

# Set connection limits
ALTER USER airrcontrol CONNECTION LIMIT 50;

# Exit psql
\q
```

### Database Backup Strategy

**Daily Backups**:
```bash
#!/bin/bash
# /opt/scripts/backup-db.sh

BACKUP_DIR="/backups/ai_arr_control"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_arr_control"
DB_HOST="db.internal"

mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump -h "$DB_HOST" -U airrcontrol "$DB_NAME" | \
  gzip > "$BACKUP_DIR/db_${TIMESTAMP}.sql.gz"

# Keep only last 30 days
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_${TIMESTAMP}.sql.gz"
```

**Cron Schedule**:
```bash
# Run daily at 2 AM
0 2 * * * /opt/scripts/backup-db.sh >> /var/log/ai_arr_control/backup.log 2>&1
```

---

## Docker Deployment

### Docker Compose Setup

```yaml
version: '3.8'

services:
  app:
    image: airrcontrol:latest
    container_name: airrcontrol
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"  # Only localhost
    environment:
      - APP_NAME=AI Arr Control
      - DEBUG=false
      - RADARR_URL=${RADARR_URL}
      - RADARR_API_KEY=${RADARR_API_KEY}
      - SONARR_URL=${SONARR_URL}
      - SONARR_API_KEY=${SONARR_API_KEY}
      - PROWLARR_URL=${PROWLARR_URL}
      - PROWLARR_API_KEY=${PROWLARR_API_KEY}
      - DATABASE_URL=postgresql+asyncpg://airrcontrol:${DB_PASSWORD}@postgres:5432/ai_arr_control
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - postgres
    networks:
      - internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:16-alpine
    container_name: airrcontrol-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=ai_arr_control
      - POSTGRES_USER=airrcontrol
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U airrcontrol"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

networks:
  internal:
    driver: bridge
```

### Deploy Docker Containers

```bash
# Set environment variables
export RADARR_URL=https://radarr.internal
export RADARR_API_KEY=xxxxx
export SONARR_URL=https://sonarr.internal
export SONARR_API_KEY=yyyyy
export PROWLARR_URL=https://prowlarr.internal
export PROWLARR_API_KEY=zzzzz
export DB_PASSWORD=strong_password_here

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Initialize database (if needed)
docker-compose exec app python -m tools.cli initdb

# Stop services
docker-compose down
```

---

## Linux/Systemd Deployment

### Create Systemd Service

Create `/etc/systemd/system/airrcontrol.service`:

```ini
[Unit]
Description=AI Arr Control - Indexer Health Management
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=notify
User=airrcontrol
Group=airrcontrol
WorkingDirectory=/opt/ai_arr_control

# Environment variables
EnvironmentFile=/opt/ai_arr_control/.env.production

# Execution
ExecStart=/opt/ai_arr_control/venv/bin/uvicorn main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --log-config logging.ini

# Restart policy
Restart=on-failure
RestartSec=10
StartLimitInterval=600s
StartLimitBurst=3

# Security settings
PrivateTmp=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/ai_arr_control /var/lib/ai_arr_control

# Resource limits
MemoryLimit=512M
CPUQuota=50%

# Standard output
StandardOutput=journal
StandardError=journal
SyslogIdentifier=airrcontrol

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable airrcontrol

# Start service
sudo systemctl start airrcontrol

# Check status
sudo systemctl status airrcontrol

# View logs
sudo journalctl -u airrcontrol -f

# Restart service
sudo systemctl restart airrcontrol

# Stop service
sudo systemctl stop airrcontrol
```

---

## Reverse Proxy Setup

### Nginx Configuration

```nginx
upstream airrcontrol {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name arr-control.example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name arr-control.example.com;

    # SSL certificates (use Let's Encrypt via certbot)
    ssl_certificate /etc/letsencrypt/live/arr-control.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/arr-control.example.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/airrcontrol_access.log;
    error_log /var/log/nginx/airrcontrol_error.log;

    # Proxy settings
    location / {
        proxy_pass http://airrcontrol;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (for monitoring)
    location /health {
        access_log off;
        proxy_pass http://airrcontrol;
    }
}
```

### Enable Nginx Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/airrcontrol /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Set up SSL with Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d arr-control.example.com
```

---

## Monitoring & Logging

### Application Logging Configuration

Create `logging.ini`:

```ini
[loggers]
keys=root

[handlers]
keys=console,file

[formatters]
keys=simple,json

[logger_root]
level=INFO
handlers=console,file

[handler_console]
class=StreamHandler
level=INFO
formatter=simple
args=(sys.stdout,)

[handler_file]
class=handlers.RotatingFileHandler
level=INFO
formatter=json
args=('/var/log/ai_arr_control/app.log', 'a', 10485760, 5)

[formatter_simple]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_json]
class=pythonjsonlogger.jsonlogger.JsonFormatter
format=%(timestamp)s %(level)s %(name)s %(message)s
```

### Monitoring Setup

**Health Check Monitoring**:
```bash
# Add to monitoring system (Prometheus, Nagios, etc.)
curl -s https://arr-control.example.com/health | jq .

# Expected response
{
  "status": "ok",
  "service": "AI Arr Control"
}
```

**Metrics Endpoint**:
```bash
curl -s https://arr-control.example.com/metrics | jq .

# Returns uptime, operation counts, success rates
{
  "uptime_seconds": 3600,
  "total_operations": 1000,
  "successful": 950,
  "failed": 50,
  "success_rate_percent": 95.0
}
```

---

## Backup & Recovery

### Backup Strategy

1. **Database Backups** (daily, retained 30 days)
2. **Configuration Backups** (.env files, encrypted)
3. **Application Logs** (rolled daily, retained 90 days)

### Recovery Procedures

**From Database Backup**:
```bash
# List available backups
ls -la /backups/ai_arr_control/

# Restore database
gunzip -c /backups/ai_arr_control/db_20241214_020000.sql.gz | \
  psql -h db.internal -U airrcontrol ai_arr_control

# Verify restoration
psql -h db.internal -U airrcontrol -d ai_arr_control -c "SELECT COUNT(*) FROM indexer_health;"
```

**Service Recovery**:
```bash
# If using systemd
sudo systemctl restart airrcontrol
sudo systemctl status airrcontrol

# If using Docker
docker-compose restart app
docker-compose logs -f app
```

---

## Troubleshooting

### Common Issues

**1. Service won't start**
```bash
# Check logs
journalctl -u airrcontrol -n 50

# Verify configuration
source /opt/ai_arr_control/.env.production
printenv | grep -i radarr

# Test connectivity to services
curl -s https://radarr.internal/api/v3/system/status
```

**2. Database connection errors**
```bash
# Check PostgreSQL
psql -h db.internal -U airrcontrol -d ai_arr_control -c "SELECT 1"

# Check connection string
echo "$DATABASE_URL"

# Verify credentials
psql -h db.internal -U postgres -c "\du"
```

**3. Indexer API errors**
```bash
# Test Radarr connection
curl -s "https://radarr.internal/api/v3/indexer" \
  -H "X-Api-Key: YOUR_KEY" | jq .

# Same for Sonarr and Prowlarr
curl -s "https://sonarr.internal/api/v3/indexer" ...
curl -s "https://prowlarr.internal/api/v3/indexer" ...
```

**4. Performance issues**
```bash
# Check resource usage
free -h                    # Memory
df -h                      # Disk
top -b -n 1 | grep python  # CPU

# Check database performance
psql -h db.internal -U airrcontrol -d ai_arr_control

# Inside psql
\timing on
SELECT COUNT(*) FROM indexer_health;
SELECT COUNT(*) FROM indexer_health WHERE timestamp > NOW() - INTERVAL '24 hours';
```

---

## Maintenance Tasks

### Weekly Tasks

- [ ] Review error logs for issues
- [ ] Check database size
- [ ] Verify backups completed successfully
- [ ] Test health check endpoints

### Monthly Tasks

- [ ] Review and update dependencies
- [ ] Check disk space usage
- [ ] Verify backup restoration
- [ ] Update SSL certificates if needed
- [ ] Review performance metrics

### Quarterly Tasks

- [ ] Plan capacity upgrades if needed
- [ ] Review and update monitoring thresholds
- [ ] Test disaster recovery procedures
- [ ] Security audit of configuration
- [ ] Document any changes made

---

**Last Updated**: December 14, 2025
**Version**: 0.4.0+
**Status**: Production Ready
