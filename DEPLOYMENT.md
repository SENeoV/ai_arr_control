# Deployment Guide

This guide covers deploying AI Arr Control in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Docker Compose Stack](#docker-compose-stack)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Considerations](#production-considerations)
6. [Monitoring and Logging](#monitoring-and-logging)

---

## Local Development

### Prerequisites

- Python 3.11+
- Radarr, Sonarr, Prowlarr instances

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ai_arr_control.git
cd ai_arr_control

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your settings
nano .env

# Run application
uvicorn main:app --reload

# In another terminal, run tests
pytest tests/
```

---

## Docker Deployment

### Single Container

```bash
# Build image
docker build -t ai-arr-control:latest .

# Run container
docker run -d \
  --name ai-arr-control \
  -p 8000:8000 \
  -v ./db:/app/db \
  -e RADARR_URL=http://radarr:7878 \
  -e RADARR_API_KEY=your_key \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=your_key \
  -e PROWLARR_URL=http://prowlarr:9696 \
  -e PROWLARR_API_KEY=your_key \
  ai-arr-control:latest

# View logs
docker logs -f ai-arr-control

# Health check
curl http://localhost:8000/health
```

### Using Docker Hub (when published)

```bash
# Pull image
docker pull yourusername/ai-arr-control:latest

# Run container
docker run -d \
  --name ai-arr-control \
  -p 8000:8000 \
  -v ./db:/app/db \
  -e RADARR_URL=http://radarr:7878 \
  -e RADARR_API_KEY=your_key \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=your_key \
  -e PROWLARR_URL=http://prowlarr:9696 \
  -e PROWLARR_API_KEY=your_key \
  yourusername/ai-arr-control:latest
```

---

## Docker Compose Stack

### Complete Stack with All Services

```bash
# Create .env file for secrets
cat > .env << EOF
RADARR_API_KEY=your_radarr_key_here
SONARR_API_KEY=your_sonarr_key_here
PROWLARR_API_KEY=your_prowlarr_key_here
EOF

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ai-arr-control

# Check status
docker-compose ps

# Stop services
docker-compose down

# Remove volumes
docker-compose down -v
```

### Service URLs

Once running with docker-compose:

- **AI Arr Control**: http://localhost:8000
- **Radarr**: http://localhost:7878
- **Sonarr**: http://localhost:8989
- **Prowlarr**: http://localhost:9696

### Configuration

Edit `docker-compose.yml` to:
- Change port mappings
- Add volume mounts for media libraries
- Adjust resource limits
- Configure logging drivers

### Environment Variables

Create `.env` file in project root:

```env
RADARR_API_KEY=your_actual_key
SONARR_API_KEY=your_actual_key
PROWLARR_API_KEY=your_actual_key
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Namespace for the application

### Create Namespace

```bash
kubectl create namespace arr-control
```

### Create Secrets

```bash
kubectl -n arr-control create secret generic arr-secrets \
  --from-literal=radarr-api-key=your_key \
  --from-literal=sonarr-api-key=your_key \
  --from-literal=prowlarr-api-key=your_key
```

### Deploy Application

Create `k8s-deployment.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: arr-config
  namespace: arr-control
data:
  RADARR_URL: "http://radarr.arr-control.svc.cluster.local:7878"
  SONARR_URL: "http://sonarr.arr-control.svc.cluster.local:8989"
  PROWLARR_URL: "http://prowlarr.arr-control.svc.cluster.local:9696"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-arr-control
  namespace: arr-control
  labels:
    app: ai-arr-control
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-arr-control
  template:
    metadata:
      labels:
        app: ai-arr-control
    spec:
      containers:
      - name: ai-arr-control
        image: yourusername/ai-arr-control:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: arr-config
        env:
        - name: RADARR_API_KEY
          valueFrom:
            secretKeyRef:
              name: arr-secrets
              key: radarr-api-key
        - name: SONARR_API_KEY
          valueFrom:
            secretKeyRef:
              name: arr-secrets
              key: sonarr-api-key
        - name: PROWLARR_API_KEY
          valueFrom:
            secretKeyRef:
              name: arr-secrets
              key: prowlarr-api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: data
          mountPath: /app/db
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: arr-control-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: ai-arr-control
  namespace: arr-control
spec:
  selector:
    app: ai-arr-control
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: arr-control-pvc
  namespace: arr-control
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

Deploy:

```bash
kubectl apply -f k8s-deployment.yaml

# Check deployment
kubectl -n arr-control get deployment
kubectl -n arr-control get pods
kubectl -n arr-control logs -f deployment/ai-arr-control

# Port forward for testing
kubectl -n arr-control port-forward svc/ai-arr-control 8000:8000
```

---

## Production Considerations

### Security

1. **API Keys**: Use Kubernetes Secrets or external vault
2. **TLS/SSL**: Use reverse proxy (nginx, traefik) with certificates
3. **Network Policies**: Restrict traffic between services
4. **Database**: For multi-instance, use PostgreSQL with strong credentials
5. **Backups**: Implement regular database backups

### Resource Management

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### High Availability

For production deployments:

1. Use multiple replicas with load balancing
2. Configure database replication (PostgreSQL)
3. Set up health checks and auto-recovery
4. Use persistent volumes for data

### Logging and Monitoring

#### ELK Stack Integration

```bash
# In docker-compose
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

#### Prometheus Metrics

Future versions will include Prometheus metrics on `/metrics` endpoint.

#### Log Aggregation

Send logs to ELK Stack or Splunk using:

```bash
docker logs --follow ai-arr-control | \
  filebeat -c filebeat.yml -e
```

---

## Monitoring and Logging

### Health Check

```bash
curl http://localhost:8000/health
# Output: {"status":"ok","service":"AI Arr Control"}
```

### Application Logs

```bash
# Docker
docker logs ai-arr-control

# Docker Compose
docker-compose logs ai-arr-control

# Kubernetes
kubectl -n arr-control logs deployment/ai-arr-control
```

### Database Access

```python
import sqlite3

conn = sqlite3.connect('db/app.db')
cursor = conn.cursor()

# Get recent health checks
cursor.execute("""
    SELECT service, name, success, error, timestamp
    FROM indexer_health
    ORDER BY timestamp DESC
    LIMIT 50
""")

for row in cursor.fetchall():
    print(row)
```

### Metrics Collection

View scheduler job stats:

```python
# In production, expose metrics via /metrics endpoint
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler: AsyncIOScheduler = app.state.scheduler
print(scheduler.get_jobs())
```

---

## Troubleshooting Deployment

### Container won't start

```bash
# Check logs
docker logs ai-arr-control

# Check configuration
docker run -it ai-arr-control env | grep ARR

# Test manually
docker run -it ai-arr-control python -c "from config.settings import settings; print(settings)"
```

### Database connection errors

```bash
# Ensure database directory is writable
docker exec ai-arr-control ls -la /app/db

# Check file permissions
docker exec ai-arr-control chmod -R 755 /app/db
```

### Services not accessible

```bash
# Test network connectivity
docker exec ai-arr-control curl http://radarr:7878/api/v3/system/status

# Check DNS
docker exec ai-arr-control nslookup radarr
```

---

## Rollback Procedure

### Docker

```bash
# If deployment fails, revert to previous image
docker pull yourusername/ai-arr-control:v0.2.0
docker stop ai-arr-control
docker rm ai-arr-control
docker run -d ... yourusername/ai-arr-control:v0.2.0
```

### Kubernetes

```bash
# View rollout history
kubectl -n arr-control rollout history deployment/ai-arr-control

# Rollback to previous version
kubectl -n arr-control rollout undo deployment/ai-arr-control
```

---

## Performance Tuning

### Database Optimization

```sql
-- For PostgreSQL (production recommended)
ANALYZE;
CREATE INDEX idx_service_timestamp ON indexer_health(service, timestamp);
CREATE INDEX idx_indexer_id ON indexer_health(indexer_id);
```

### Application Configuration

```env
# Adjust scheduler intervals
# Default: health check every 30 min, autoheal every 2 hours
# Edit in main.py scheduler.add_job() calls
```

### Resource Limits

Start with:
```
CPU: 250m request / 500m limit
RAM: 256Mi request / 512Mi limit
```

Monitor and adjust based on actual usage.

---

For additional help, see [README.md](README.md) and check GitHub issues.
