## Quick Start Guide

Get AI Arr Control running in 5 minutes.

---

## Prerequisites

- Python 3.11+
- Radarr, Sonarr, and Prowlarr instances (with API keys)
- Optional: Docker

---

## Option 1: Docker (Easiest)

### 1. Create `.env` file

```bash
cp .env.example .env

# Edit with your values
cat .env
```

Fill in:
```env
RADARR_URL=http://radarr:7878
RADARR_API_KEY=abc123...

SONARR_URL=http://sonarr:8989
SONARR_API_KEY=def456...

PROWLARR_URL=http://prowlarr:9696
PROWLARR_API_KEY=ghi789...
```

### 2. Run with Docker

```bash
# Build image
docker build -t ai-arr-control:latest .

# Run container
docker run -d \
  --name ai-arr-control \
  --env-file .env \
  -p 8000:8000 \
  -v ./db:/app/db \
  ai-arr-control:latest

# Check status
docker logs ai-arr-control
```

### 3. Access Application

- **Web UI**: http://localhost:8000/docs
- **Health check**: `curl http://localhost:8000/health`
- **Indexers**: `curl http://localhost:8000/indexers`

---

## Option 2: Python (Manual)

### 1. Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ai_arr_control.git
cd ai_arr_control

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .
```

### 2. Configure

```bash
# Copy and edit configuration
cp .env.example .env
nano .env  # Edit with your settings
```

### 3. Run

```bash
# Start the application
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Access at: `http://localhost:8000`

---

## Option 3: Docker Compose (Full Stack)

```bash
# Create .env file
cp .env.example .env
nano .env

# Start stack
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
curl http://localhost:8000/health
```

---

## Verify It's Working

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"ok","service":"AI Arr Control"}
```

### 2. View Indexers

```bash
curl http://localhost:8000/indexers | jq
```

Expected: List of indexers from Radarr and Sonarr

### 3. Check Startup Status

```bash
curl http://localhost:8000/startup-status | jq
```

Expected: `"complete": true`

### 4. API Documentation

Open in browser: `http://localhost:8000/docs`

---

## Common Tasks

### Manually Run Health Check

```bash
curl -X POST http://localhost:8000/agents/health/run
```

### Disable a Failing Indexer

```bash
# First, list indexers to find ID
curl http://localhost:8000/indexers/radarr | jq '.indexers[] | {id, name}'

# Then disable (e.g., indexer ID 2)
curl -X POST http://localhost:8000/indexers/radarr/2/disable
```

### Enable an Indexer

```bash
curl -X POST http://localhost:8000/indexers/radarr/2/enable
```

### View Recent Events

```bash
curl http://localhost:8000/events | jq
```

### Check Application Metrics

```bash
curl http://localhost:8000/metrics | jq
```

---

## Troubleshooting

### Connection Error to Radarr/Sonarr/Prowlarr

1. Verify URLs and API keys in `.env`
2. Test manually:
   ```bash
   curl http://radarr:7878/api/v3/system/status
   ```
3. Check if services are running
4. Check firewall/network

### Application Won't Start

1. Check logs:
   ```bash
   docker logs ai-arr-control
   # or
   tail -f ai_arr_control.log
   ```

2. Verify `.env` file is present and valid
3. Ensure database directory is writable

### Database Lock (SQLite)

```bash
# Stop application
docker stop ai-arr-control

# Remove lock files
rm db/app.db-journal db/app.db-shm db/app.db-wal 2>/dev/null || true

# Restart
docker start ai-arr-control
```

### Port Already in Use

```bash
# Use different port
docker run -p 8001:8000 ai-arr-control:latest

# Or find and kill process using port 8000
lsof -i :8000
kill -9 <PID>
```

---

## Next Steps

1. **Read the full documentation**:
   - [API Reference](API.md) - All endpoints explained
   - [Configuration](INSTALL.md) - Configuration options
   - [Deployment](PRODUCTION.md) - Production setup
   - [Troubleshooting](TROUBLESHOOTING.md) - Common issues

2. **Configure health checks**:
   - By default, health checks run every 30 minutes
   - Auto-heal runs every 2 hours
   - Modify in `main.py` if needed

3. **Monitor performance**:
   - Visit `/metrics` for uptime and operation stats
   - Check `/health-history` for historical data
   - Review `/events` for recent system events

4. **Set up backups**:
   - See [PRODUCTION.md](PRODUCTION.md) for backup procedures
   - Database is in `db/app.db` (SQLite)
   - Events log is in `logs/events.jsonl`

5. **Enable discovery** (optional):
   ```env
   DISCOVERY_ENABLED=true
   DISCOVERY_SOURCES=https://example.com/indexers.json
   ```

---

## Configuration Reference

| Setting | Required | Default | Purpose |
|---------|----------|---------|---------|
| `RADARR_URL` | Yes | - | Radarr instance URL |
| `RADARR_API_KEY` | Yes | - | Radarr API key |
| `SONARR_URL` | Yes | - | Sonarr instance URL |
| `SONARR_API_KEY` | Yes | - | Sonarr API key |
| `PROWLARR_URL` | Yes | - | Prowlarr instance URL |
| `PROWLARR_API_KEY` | Yes | - | Prowlarr API key |
| `DATABASE_URL` | No | SQLite | Database connection string |
| `DEBUG` | No | `false` | Enable verbose logging |
| `DISCOVERY_ENABLED` | No | `false` | Enable indexer discovery |
| `DISCOVERY_SOURCES` | No | - | URLs to fetch indexers from |

---

## API Endpoints (Quick Reference)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check |
| `GET` | `/indexers` | List all indexers |
| `GET` | `/indexers/{service}` | Indexers for service |
| `POST` | `/indexers/{service}/{id}/test` | Test indexer |
| `POST` | `/indexers/{service}/{id}/disable` | Disable indexer |
| `POST` | `/indexers/{service}/{id}/enable` | Enable indexer |
| `GET` | `/metrics` | Application metrics |
| `GET` | `/agents/status` | Agent status |
| `GET` | `/events` | Recent events |
| `POST` | `/agents/health/run` | Run health check manually |

Full API docs: `http://localhost:8000/docs` (Swagger UI)

---

## Support

- **Documentation**: See [README.md](README.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Deployment**: See [PRODUCTION.md](PRODUCTION.md)
- **API Reference**: See [API.md](API.md)
- **Build & Test**: See [BUILD.md](BUILD.md)

---

## Need Help?

1. **Check logs**:
   ```bash
   docker logs ai-arr-control
   # or
   tail -f ai_arr_control.log
   ```

2. **Test endpoints**:
   ```bash
   curl http://localhost:8000/startup-status | jq
   curl http://localhost:8000/agents/status | jq
   ```

3. **Review troubleshooting guide**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

4. **Check configuration**: Ensure `.env` has all required values

---

**You're all set! AI Arr Control is now running.** 🎉

Visit `http://localhost:8000/docs` to explore the API or `http://localhost:8000` for service info.
