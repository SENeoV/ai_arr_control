# AI Arr Control

> **Autonomous agent platform for intelligent indexer health monitoring and remediation in Radarr, Sonarr, and Prowlarr**

AI Arr Control is a production-ready system that continuously monitors your media indexer health, automatically detects failing indexers, and intelligently disables them to prevent download stalls and search failures. Built with modern async Python, comprehensive error handling, and professional observability.

## Features

### Core Capabilities
- ✅ **Autonomous Monitoring**: Periodic health checks every 30 minutes with automatic indexer testing
- ✅ **Intelligent Remediation**: Automatically disables failing indexers to prevent service degradation
- ✅ **Persistent Audit Trail**: Complete history of health checks and changes in SQLite/PostgreSQL
- ✅ **Event Logging**: Structured event log with detailed health metrics and diagnostics
- ✅ **RESTful API**: Full-featured HTTP API for manual control and integration
- ✅ **Async-First**: Built on FastAPI with proper async/await patterns for high concurrency
- ✅ **Type-Safe**: Full type hints throughout for IDE support and static analysis
- ✅ **Production-Ready**: Error handling, logging, configuration validation, and graceful shutdown

### Additional Features  
- **Metrics & Observability**: Track success rates, uptime, and operation history
- **Discovery Support**: Optional indexer discovery from external sources
- **CLI Tools**: Command-line interface for administrative tasks
- **Scheduler Control**: Real-time status of background jobs and agents
- **Multiple Databases**: Works with SQLite, PostgreSQL, MySQL, and other SQLAlchemy backends

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Application (0.4.0)                │
│                                                             │
│  Agents:                                                   │
│  ├─ IndexerHealthAgent (every 30 min) → read-only checks  │
│  ├─ IndexerAutoHealAgent (every 2 hrs) → remediation      │
│  ├─ IndexerControlAgent → state changes                   │
│  └─ IndexerDiscoveryAgent → new indexer detection         │
│                                                             │
│  Services:                                                  │
│  ├─ RadarrService → Radarr API wrapper                    │
│  ├─ SonarrService → Sonarr API wrapper                    │
│  └─ ProwlarrService → Prowlarr API wrapper                │
│                                                             │
│  Storage:                                                   │
│  └─ SQLAlchemy ORM → IndexerHealth audit table            │
└─────────────────────────────────────────────────────────────┘
         ↓                      ↓                      ↓
    ┌──────────┐          ┌──────────┐          ┌──────────┐
    │  Radarr  │          │  Sonarr  │          │ Prowlarr │
    │ (Movies) │          │  (TV)    │          │(Indexers)│
    └──────────┘          └──────────┘          └──────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+ (tested with 3.11, 3.12, 3.13)
- Radarr instance with API key (required)
- Sonarr instance with API key (required)
- Prowlarr instance with API key (required)

### Installation (5 minutes)

```bash
# Clone and enter directory
git clone https://github.com/yourusername/ai_arr_control.git
cd ai_arr_control

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install package
pip install -e ".[dev]"  # Include dev tools like pytest

# Configure environment
cp .env.example .env
nano .env  # Edit with your Radarr, Sonarr, Prowlarr URLs and API keys

# Initialize database
python -m tools.cli initdb

# Run the application
uvicorn main:app --host 0.0.0.0 --port 8000
```

Access the API at `http://localhost:8000`

**Health check**: `curl http://localhost:8000/health`

**API documentation**: `http://localhost:8000/docs` (Swagger UI)

## Configuration

### Environment Variables

All settings are loaded from `.env` file or environment variables (case-insensitive).

#### Required Configuration

```env
# Radarr Service
RADARR_URL=http://radarr:7878
RADARR_API_KEY=your_api_key

# Sonarr Service
SONARR_URL=http://sonarr:8989
SONARR_API_KEY=your_api_key

# Prowlarr Service
PROWLARR_URL=http://prowlarr:9696
PROWLARR_API_KEY=your_api_key
```

#### Optional Configuration

```env
# Application Settings
APP_NAME=AI Arr Control
DEBUG=false

# Database (defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///./db/app.db
# For PostgreSQL: postgresql+asyncpg://user:password@localhost:5432/dbname

# Indexer Discovery
DISCOVERY_ENABLED=false
DISCOVERY_SOURCES=https://example.com/indexers.json
DISCOVERY_INTERVAL_HOURS=24
DISCOVERY_ADD_TO_PROWLARR=false
```

### Getting API Keys

**Radarr**:
1. Settings → General → Security → API Key

**Sonarr**:
1. Settings → General → Security → API Key

**Prowlarr**:
1. Settings → General → Security → API Key

## API Reference

### Health & Status

```
GET /health                      # Health check
GET /                            # Service info and endpoints
GET /metrics                     # Application metrics
GET /agents/status              # Scheduler and agent status
```

### Indexer Management

```
GET  /indexers                           # List all indexers
GET  /indexers/{service}                # Indexers for service
GET  /indexers/stats                    # Indexer statistics
POST /indexers/{service}/{id}/test      # Test indexer
POST /indexers/{service}/{id}/enable    # Enable indexer
POST /indexers/{service}/{id}/disable   # Disable indexer
```

### Monitoring & Analytics

```
GET /health-history              # Health check history (24 hours default)
GET /stats/detailed              # Detailed statistics (7 days)
GET /events                      # Recent system events
```

### Manual Agent Control

```
POST /agents/health/run          # Run health check immediately
POST /agents/autoheal/run        # Run autoheal cycle immediately
POST /agents/discovery/run       # Run discovery immediately
```

All endpoints return JSON. See `/docs` for interactive Swagger documentation.

## Usage Examples

### Check System Health

```bash
curl http://localhost:8000/health
# Response:
# {"status": "ok", "service": "AI Arr Control"}
```

### View All Indexers

```bash
curl http://localhost:8000/indexers | jq
```

### Manually Disable an Indexer

```bash
curl -X POST http://localhost:8000/indexers/radarr/5/disable
# Response:
# {"success": true, "service": "radarr", "indexer_id": 5, "action": "disabled"}
```

### View Health History

```bash
curl 'http://localhost:8000/health-history?hours=24&limit=50' | jq
```

### Check Metrics

```bash
curl http://localhost:8000/metrics | jq
```

### View Recent Events

```bash
curl 'http://localhost:8000/events?limit=20' | jq
```

## Command-Line Interface

### Setup and Maintenance

```bash
# Initialize database
python -m tools.cli initdb

# Run application (foreground)
python -m tools.cli run --host 0.0.0.0 --port 8000

# Run detached (background)
python -m tools.cli run --detach --port 8000

# Stop background server
python -m tools.cli stop

# Check status
python -m tools.cli status

# Show version
python -m tools.cli version
```

### Development Commands

```bash
# Run smoke tests
python -m tools.cli check

# Run full test suite
python -m tools.cli tests

# Run with auto-reload
python -m tools.cli run --reload
```

## Deployment

### Docker

Build and run using provided Dockerfile:

```bash
docker build -t ai-arr-control:latest .
docker run -d \
  -e RADARR_URL=http://radarr:7878 \
  -e RADARR_API_KEY=your_key \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=your_key \
  -e PROWLARR_URL=http://prowlarr:9696 \
  -e PROWLARR_API_KEY=your_key \
  -p 8000:8000 \
  ai-arr-control:latest
```

### Docker Compose

Use the provided `docker-compose.yml`:

```bash
docker-compose up -d
```

### Kubernetes

See [DEPLOYMENT.md](DEPLOYMENT.md) for Kubernetes deployment instructions.

### Systemd Service

Create `/etc/systemd/system/ai-arr-control.service`:

```ini
[Unit]
Description=AI Arr Control
After=network.target

[Service]
Type=simple
User=ai-arr
WorkingDirectory=/opt/ai-arr-control
ExecStart=/opt/ai-arr-control/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ai-arr-control
sudo systemctl start ai-arr-control
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/ai_arr_control.git
cd ai_arr_control

python -m venv venv
source venv/bin/activate

pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_agents.py

# Run in watch mode (requires pytest-watch)
ptw tests/
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy agents/ services/ config/ core/ db/
```

### Running Locally

```bash
# Setup .env with test values
cp .env.example .env

# Initialize database
python -m tools.cli initdb

# Run in reload mode
uvicorn main:app --reload

# Or use CLI
python -m tools.cli run --reload
```

## Troubleshooting

### Connection Failures

**Problem**: `Connection error` when connecting to Radarr/Sonarr

**Solutions**:
1. Verify URLs are correct: `RADARR_URL=http://host:port` (no trailing slash)
2. Check API keys are correct
3. Ensure services are accessible from the host running AI Arr Control
4. If behind proxy, configure accordingly
5. Check firewall rules

### Database Issues

**Problem**: `sqlite3.OperationalError: unable to open database file`

**Solutions**:
1. Ensure `db/` directory is writable: `mkdir -p db && chmod 755 db`
2. For PostgreSQL, verify connection string is correct
3. Check database user has proper permissions

### High CPU Usage

**Problem**: Application consuming excessive CPU

**Solutions**:
1. Check scheduler job intervals are reasonable
2. Verify API responses are returning reasonable data
3. Look for infinite loops or recursion in custom code
4. Monitor with `top` or `htop` to identify bottleneck

### Memory Issues

**Problem**: Memory usage growing over time

**Solutions**:
1. Ensure database connections are properly closed
2. Check for large response objects not being garbage collected
3. Monitor with `ps aux | grep python`
4. Consider reducing health check frequency or database retention

## Architecture & Design

### Agent Framework

The system uses an extensible agent pattern:

- **IndexerHealthAgent**: Read-only monitoring, no changes
- **IndexerAutoHealAgent**: Testing + remediation (disables failures)
- **IndexerControlAgent**: Low-level enable/disable operations
- **IndexerDiscoveryAgent**: Optional external indexer discovery

Agents run on configured schedules via APScheduler.

### Database Schema

- **IndexerHealth**: Historical records of health check results
  - Fields: service, indexer_id, name, success, error, timestamp
  - Indexes: (service, timestamp), (indexer_id)
  - Retention: Indefinite (consider archiving for long-term storage)

### Error Handling

All components implement:
- Try-catch-log pattern for graceful degradation
- Detailed error logging with context
- Structured exception messages
- Timeout protection on external calls

### Logging

Structured logging using Loguru with:
- Color-coded output for easy reading
- Context (module, function, line number)
- Optional debug mode for verbose output
- Optional file logging (see `core/logging.py`)

## Performance Considerations

### Health Check Frequency

Default schedules:
- Health checks: Every 30 minutes (read-only, minimal impact)
- Autoheal: Every 2 hours (includes disable operations)

Adjust in `main.py` scheduler configuration if needed.

### Database Size

IndexerHealth table grows over time:
- ~200 bytes per record
- ~48 records per indexer per day (every 30 min check)
- For 50 indexers: ~480K per day, ~175MB per year

Consider:
- Archiving old records to separate table
- Reducing retention period
- Using PostgreSQL for better scaling

### API Timeouts

Default HTTP timeout: 30 seconds

Adjust in `ArrHttpClient` initialization if needed.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Changelog

See [CHANGES.md](CHANGES.md) for version history.

## License

This project is released under the [Unlicense](LICENSE) - free and unencumbered software.

## Support

For issues, questions, or feature requests:

1. Check [TROUBLESHOOTING.md](DEPLOYMENT.md#troubleshooting) section in deployment guide
2. Open an issue on GitHub
3. Check existing issues for similar problems
4. Include logs, configuration (without API keys), and steps to reproduce

---

**Made for media enthusiasts by media enthusiasts.** 🎬📺
