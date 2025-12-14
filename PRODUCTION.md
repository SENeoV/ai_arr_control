## Production Deployment Guide

Complete guide for deploying AI Arr Control to production environments.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Docker Deployment](#docker-deployment)
3. [Docker Compose Stack](#docker-compose-stack)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Reverse Proxy Configuration](#reverse-proxy-configuration)
6. [Database Setup](#database-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Security Hardening](#security-hardening)

---

## Pre-Deployment Checklist

- [ ] All required environment variables configured
- [ ] Database is accessible and initialized
- [ ] Radarr, Sonarr, and Prowlarr instances verified reachable
- [ ] SSL/TLS certificates obtained (if using HTTPS)
- [ ] Firewall rules configured to allow app traffic
- [ ] Backup strategy documented
- [ ] Monitoring/alerting configured
- [ ] Log collection configured
- [ ] Disaster recovery plan established
- [ ] Load balancer health check path confirmed (`/health`)

---

## Docker Deployment

### Build Image

```bash
# Build for production
docker build -t ai-arr-control:latest .

# Or with specific version tag
docker build -t ai-arr-control:v0.4.0 .
docker tag ai-arr-control:v0.4.0 ai-arr-control:latest
```

### Run Container

```bash
docker run -d \
  --name ai-arr-control \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file /etc/ai-arr-control/.env \
  -v /var/lib/ai-arr-control/db:/app/db \
  -v /var/log/ai-arr-control:/app/logs \
  --health-cmd="curl -f http://localhost:8000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --health-start-period=30s \
  ai-arr-control:latest
```

### Monitor Container

```bash
# View logs
docker logs -f ai-arr-control

# Check health
docker inspect --format='{{.State.Health.Status}}' ai-arr-control

# Get stats
docker stats ai-arr-control

# Stop gracefully
docker stop ai-arr-control

# Remove container
docker rm ai-arr-control
```

---

## Docker Compose Stack

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  ai-arr-control:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-arr-control
    restart: unless-stopped
    
    # Port mapping
    ports:
      - "8000:8000"
    
    # Environment configuration
    env_file:
      - .env.production
    environment:
      - DEBUG=false
    
    # Volume mounts
    volumes:
      - ./db:/app/db
      - ./logs:/app/logs
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    
    # Network
    networks:
      - arr_network
    
    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  # Optional: PostgreSQL database
  postgres:
    image: postgres:15-alpine
    container_name: ai-arr-postgres
    restart: unless-stopped
    
    environment:
      POSTGRES_DB: ai_arr_control
      POSTGRES_USER: ai_arr
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
    networks:
      - arr_network
    
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_arr"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  arr_network:
    driver: bridge

volumes:
  postgres_data:
```

### Deploy with Docker Compose

```bash
# Create production directory
mkdir -p /opt/ai-arr-control
cd /opt/ai-arr-control

# Copy files
cp docker-compose.yml docker-compose.yml
cp .env.example .env.production

# Edit configuration
nano .env.production

# Start stack
docker-compose up -d

# View logs
docker-compose logs -f ai-arr-control

# Stop stack
docker-compose down
```

---

## Kubernetes Deployment

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: arr-control
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-arr-control-config
  namespace: arr-control
data:
  DEBUG: "false"
  APP_NAME: "AI Arr Control"
  DISCOVERY_ENABLED: "false"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-arr-control-secret
  namespace: arr-control
type: Opaque
stringData:
  radarr-url: "http://radarr:7878"
  radarr-api-key: "YOUR_KEY_HERE"
  sonarr-url: "http://sonarr:8989"
  sonarr-api-key: "YOUR_KEY_HERE"
  prowlarr-url: "http://prowlarr:9696"
  prowlarr-api-key: "YOUR_KEY_HERE"
  database-url: "postgresql+asyncpg://user:password@postgres:5432/ai_arr_control"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-arr-control
  namespace: arr-control
  labels:
    app: ai-arr-control
spec:
  replicas: 1  # Use 1 for single scheduler
  selector:
    matchLabels:
      app: ai-arr-control
  
  template:
    metadata:
      labels:
        app: ai-arr-control
    
    spec:
      serviceAccountName: ai-arr-control
      
      containers:
      - name: ai-arr-control
        image: ai-arr-control:latest
        imagePullPolicy: Always
        
        # Ports
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        
        # Environment variables
        envFrom:
        - configMapRef:
            name: ai-arr-control-config
        
        env:
        - name: RADARR_URL
          valueFrom:
            secretKeyRef:
              name: ai-arr-control-secret
              key: radarr-url
        - name: RADARR_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-arr-control-secret
              key: radarr-api-key
        - name: SONARR_URL
          valueFrom:
            secretKeyRef:
              name: ai-arr-control-secret
              key: sonarr-url
        - name: SONARR_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-arr-control-secret
              key: sonarr-api-key
        - name: PROWLARR_URL
          valueFrom:
            secretKeyRef:
              name: ai-arr-control-secret
              key: prowlarr-url
        - name: PROWLARR_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-arr-control-secret
              key: prowlarr-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ai-arr-control-secret
              key: database-url
        
        # Resources
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /startup-status
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Volumes
        volumeMounts:
        - name: db
          mountPath: /app/db
        - name: logs
          mountPath: /app/logs
      
      volumes:
      - name: db
        persistentVolumeClaim:
          claimName: ai-arr-control-db
      - name: logs
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: ai-arr-control
  namespace: arr-control
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: http
    protocol: TCP
  selector:
    app: ai-arr-control

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ai-arr-control-db
  namespace: arr-control
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace arr-control

# Create secrets
kubectl create secret generic ai-arr-control-secret \
  -n arr-control \
  --from-literal=radarr-api-key=YOUR_KEY \
  --from-literal=sonarr-api-key=YOUR_KEY \
  --from-literal=prowlarr-api-key=YOUR_KEY

# Apply manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -n arr-control
kubectl logs -n arr-control deployment/ai-arr-control
```

---

## Reverse Proxy Configuration

### Nginx

```nginx
upstream ai_arr_control {
    server localhost:8000;
}

server {
    listen 80;
    server_name indexer-control.example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name indexer-control.example.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/indexer-control.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/indexer-control.example.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
    
    # Proxy settings
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://ai_arr_control;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint for load balancer
    location /health {
        proxy_pass http://ai_arr_control/health;
        access_log off;
    }
}
```

### Apache

```apache
<VirtualHost *:443>
    ServerName indexer-control.example.com
    
    # SSL
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/indexer-control.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/indexer-control.example.com/privkey.pem
    
    # Security headers
    Header always set Strict-Transport-Security "max-age=31536000"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "DENY"
    
    # Proxy settings
    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/
    
    # WebSocket support
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://localhost:8000/$1" [P,L]
</VirtualHost>

<VirtualHost *:80>
    ServerName indexer-control.example.com
    Redirect / https://indexer-control.example.com/
</VirtualHost>
```

---

## Database Setup

### PostgreSQL Production Setup

```bash
# 1. Create database
sudo -u postgres createdb ai_arr_control

# 2. Create user
sudo -u postgres createuser ai_arr --pwprompt

# 3. Grant permissions
sudo -u postgres psql << EOF
ALTER ROLE ai_arr WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_arr_control TO ai_arr;
ALTER DATABASE ai_arr_control OWNER TO ai_arr;
EOF

# 4. Connection string for .env
DATABASE_URL=postgresql+asyncpg://ai_arr:secure_password@localhost:5432/ai_arr_control

# 5. Test connection
psql -U ai_arr -d ai_arr_control -c "SELECT 1"
```

### MySQL Production Setup

```bash
# 1. Create database and user
mysql -u root -p << EOF
CREATE DATABASE ai_arr_control CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ai_arr'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON ai_arr_control.* TO 'ai_arr'@'localhost';
FLUSH PRIVILEGES;
EOF

# 2. Connection string for .env
DATABASE_URL=mysql+aiomysql://ai_arr:secure_password@localhost:3306/ai_arr_control

# 3. Test connection
mysql -u ai_arr -p ai_arr_control -e "SELECT 1"
```

### Backup Strategy

```bash
#!/bin/bash
# Daily PostgreSQL backup

BACKUP_DIR="/backups/ai-arr-control"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U ai_arr ai_arr_control | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup application data
tar czf $BACKUP_DIR/data_$TIMESTAMP.tar.gz /var/lib/ai-arr-control/db

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-ai-arr-control.sh
```

---

## Monitoring & Logging

### Prometheus Metrics (Future Enhancement)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ai-arr-control'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### ELK Stack Logging

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/ai-arr-control/ai_arr_control.log
    - /var/log/ai-arr-control/events.jsonl

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

processors:
  - add_kubernetes_metadata:
      in_cluster: true
```

### Alerting (via monitoring)

Monitor these key endpoints:

- `GET /health` - Basic health
- `GET /startup-status` - Startup completion
- `GET /agents/status` - Agent health
- Response time > 5s
- Error rate > 5%

---

## Security Hardening

### SSL/TLS

```bash
# Obtain certificates with Let's Encrypt
sudo certbot certonly --standalone -d indexer-control.example.com

# Auto-renew
sudo certbot renew --quiet
```

### API Authentication (Future Enhancement)

Currently the API is open. Consider adding:

```python
# Bearer token authentication
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/indexers")
async def list_indexers(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    # Validate token
    if not validate_token(token):
        raise HTTPException(status_code=401)
    return indexers
```

### Network Security

```bash
# UFW firewall example
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Environment Variable Security

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets management (e.g., HashiCorp Vault)
# Or container orchestration secrets (K8s secrets, Docker secrets)

# Rotate API keys regularly
```

---

## Update & Maintenance

### Rolling Updates

```bash
# 1. Pull new image
docker pull ai-arr-control:latest

# 2. Stop old container gracefully
docker stop -t 30 ai-arr-control

# 3. Remove old container
docker rm ai-arr-control

# 4. Start new container
docker run -d --name ai-arr-control ... ai-arr-control:latest

# 5. Verify health
curl http://localhost:8000/health
```

### Database Migrations

```bash
# Backup before upgrade
pg_dump -U ai_arr ai_arr_control > backup.sql

# Run application (auto-creates tables)
docker run ... ai-arr-control:latest

# If needed, restore
psql -U ai_arr ai_arr_control < backup.sql
```

---

## Health Checks & Verification

```bash
# Health endpoint
curl -f https://indexer-control.example.com/health || exit 1

# Startup status
curl -s https://indexer-control.example.com/startup-status | jq '.complete'

# Agent status
curl -s https://indexer-control.example.com/agents/status | jq '.scheduler.running'

# API responsiveness
time curl -s https://indexer-control.example.com/indexers > /dev/null
```

---

## Performance Optimization

### Connection Pooling (PostgreSQL)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?pool_size=20&max_overflow=40
```

### Caching Configuration

```env
HEALTH_CHECK_CACHE_TTL_SECONDS=600
HEALTH_CHECK_CACHE_MAX_ENTRIES=10000
```

### Load Distribution

For multiple instances, use:
- Round-robin load balancer
- Session affinity (optional)
- Shared database backend
- Centralized logging

---

## Disaster Recovery

### Recovery Procedure

```bash
# 1. Check backup integrity
tar tzf /backups/data_latest.tar.gz | head

# 2. Restore database
psql -U ai_arr ai_arr_control < /backups/db_latest.sql

# 3. Restore application data
tar xzf /backups/data_latest.tar.gz

# 4. Verify integrity
curl http://localhost:8000/health

# 5. Run health checks
curl http://localhost:8000/startup-status
```

### RTO/RPO Targets

- **Recovery Time Objective (RTO)**: < 15 minutes
- **Recovery Point Objective (RPO)**: < 1 hour
