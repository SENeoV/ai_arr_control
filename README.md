# AI Arr Control

**Autonomous AI agent platform for intelligent indexer management and health monitoring in Radarr, Sonarr, and Prowlarr.**

AI Arr Control is a production-grade system that automatically monitors media indexer health across your Radarr and Sonarr installations, tests connectivity, and intelligently disables broken indexers to prevent stalled downloads and search failures. Built with modern Python async patterns, comprehensive error handling, and professional-grade logging.

---

## Features

### Core Functionality
- **Autonomous Health Monitoring**: Periodic health checks of all configured indexers (every 30 minutes)
- **Automated Healing**: Automatically disables failing indexers to prevent service degradation (every 2 hours)
- **Persistent Audit Trail**: Stores all health check results in database for trend analysis and debugging
- **Event Logging**: Structured, professional logging with timestamps, service names, and error messages
- **FastAPI Foundation**: Lightweight, async-first architecture with built-in health endpoints and API documentation

### Production-Ready
- ✅ Comprehensive error handling and graceful degradation
- ✅ Proper resource management (async context managers, connection pooling)
- ✅ Type hints throughout codebase for IDE support and type safety
- ✅ Comprehensive docstrings and inline comments
- ✅ Database migration ready (tested with SQLite, PostgreSQL-compatible)
- ✅ Configuration validation at startup
- ✅ Extensible agent framework for custom behaviors
- ✅ Full async/await pattern for non-blocking operations

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  IndexerHealthAgent (every 30 min)                     │  │
│  │  ✓ Read-only health checks                            │  │
│  │  ✓ Tests all indexers in Radarr & Sonarr             │  │
│  │  ✓ Logs results (no database writes)                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  IndexerAutoHealAgent (every 2 hours)                  │  │
│  │  ✓ Tests all indexers thoroughly                      │  │
│  │  ✓ Records results in database                        │  │
│  │  ✓ Automatically disables failing indexers            │  │
│  │  ✓ Delegates control to IndexerControlAgent          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Database Layer (SQLite / PostgreSQL-compatible)       │  │
│  │  ✓ Stores health check history                        │  │
│  │  ✓ Enables trend analysis and debugging              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
              ↓                    ↓                    ↓
         ┌─────────┐         ┌─────────┐         ┌──────────┐
         │  Radarr │         │  Sonarr │         │ Prowlarr │
         │ (Movies)│         │  (TV)   │         │(Indexers)│
         └─────────┘         └─────────┘         └──────────┘
```

### Component Overview

| Component | Purpose | Frequency |
|-----------|---------|-----------|
| **IndexerHealthAgent** | Read-only health monitoring | Every 30 minutes |
| **IndexerAutoHealAgent** | Comprehensive testing, database logging, auto-remediation | Every 2 hours |
| **IndexerControlAgent** | Low-level primitives for enabling/disabling indexers | On-demand |
| **Services Layer** | HTTP wrappers for Radarr, Sonarr, Prowlarr APIs | Event-driven |
| **Database** | SQLite-based audit trail and health history | Event-driven |

---

## Quick Start

### Prerequisites

- **Python 3.11+** (tested with 3.11+)
- **Radarr** instance with API key (required)
- **Sonarr** instance with API key (required)
- **Prowlarr** instance with API key (optional but recommended)

All Arr services must be accessible from the host running AI Arr Control.

### Installation (5 minutes)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ai_arr_control.git
   cd ai_arr_control
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Radarr, Sonarr, Prowlarr URLs and API keys
   nano .env
   ```

5. **Run the application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

The application will:
- Initialize the database
- Connect to all configured Arr services
- Start the scheduler with both agents
- Listen on `http://localhost:8000`

Check health: `curl http://localhost:8000/health`

---

## Configuration

### Environment Variables

All configuration is loaded from the `.env` file or environment variables.

#### Required Variables

```env
# Radarr (Movie Indexer Management)
RADARR_URL=http://radarr:7878
RADARR_API_KEY=your_radarr_api_key_here

# Sonarr (TV Show Indexer Management)
SONARR_URL=http://sonarr:8989
SONARR_API_KEY=your_sonarr_api_key_here

# Prowlarr (Unified Indexer Manager - required but may have limited use)
PROWLARR_URL=http://prowlarr:9696
PROWLARR_API_KEY=your_prowlarr_api_key_here
```

#### Optional Variables

```env
# Application Settings
APP_NAME=AI Arr Control           # Display name (default: AI Arr Control)
DEBUG=false                       # Enable debug logging (default: false)

# Database (defaults to SQLite in db/app.db)
# For production, consider PostgreSQL:
DATABASE_URL=sqlite+aiosqlite:///./db/app.db
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_arr_control
```

### How to Get API Keys

1. **Radarr**: Settings → General → Security → API Key
2. **Sonarr**: Settings → General → Security → API Key
3. **Prowlarr**: Settings → General → Security → API Key

**Note:** Ensure each API key has the minimum required permissions for indexer management.

### Docker / Docker Compose Example

```yaml
version: '3.8'
services:
  ai-arr-control:
    build: .
    container_name: ai-arr-control
    ports:
      - "8000:8000"
    environment:
      RADARR_URL: http://radarr:7878
      RADARR_API_KEY: your_key_here
      SONARR_URL: http://sonarr:8989
      SONARR_API_KEY: your_key_here
      PROWLARR_URL: http://prowlarr:9696
      PROWLARR_API_KEY: your_key_here
      DEBUG: "false"
    depends_on:
      - radarr
      - sonarr
      - prowlarr
    restart: unless-stopped
```

---

## Usage

### Health Check Endpoint

Monitor application status:

```bash
curl http://localhost:8000/health
# Output: {"status":"ok","service":"AI Arr Control"}
```

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Accessing Logs

The application outputs structured logs to stdout:

```
INFO     | main:lifespan:60 - Starting AI Arr Control
INFO     | core.logging:add_file_logging:45 - Database initialization successful
INFO     | agents.indexer_health_agent:run:50 - Starting health check cycle
INFO     | services.radarr:get_indexers:43 - Fetching Radarr indexers
DEBUG    | services.radarr:test_indexer:64 - Testing Radarr indexer 1
INFO     | agents.indexer_health_agent:run:68 - Radarr indexer 'NZBGeek' OK
INFO     | agents.indexer_autoheal_agent:run:75 - Starting autoheal cycle
WARNING  | agents.indexer_autoheal_agent:run:110 - Indexer radarr/FailedIndexer failed health check: Connection timeout
WARNING  | agents.indexer_control_agent:disable_indexer:58 - Disabled indexer: FailedIndexer
```

### Querying Health History

Access the database to analyze trends:

```python
import sqlite3

conn = sqlite3.connect('db/app.db')
cursor = conn.cursor()

# Last 20 health checks for Radarr
cursor.execute("""
    SELECT service, name, success, error, timestamp 
    FROM indexer_health 
    WHERE service = 'radarr' 
    ORDER BY timestamp DESC 
    LIMIT 20
""")

for service, name, success, error, ts in cursor.fetchall():
    status = "✓ OK" if success else f"✗ FAILED: {error}"
    print(f"{ts} | {service}/{name}: {status}")
```

### Schedule Overview

| Agent | Interval | Purpose | Impact |
|-------|----------|---------|--------|
| **IndexerHealthAgent** | Every 30 min | Quick read-only health check | Logs only, no DB writes |
| **IndexerAutoHealAgent** | Every 2 hours | Comprehensive test + remediation | May disable failed indexers |

To customize schedules, edit the `scheduler.add_job()` calls in [main.py](main.py).

---

## Project Structure

```
ai_arr_control/
├── main.py                         # FastAPI app & scheduler initialization
├── pyproject.toml                  # Package metadata, dependencies, tool configs
├── .env.example                    # Configuration template (RENAME TO .env)
├── .gitignore                      # Git exclusions
├── LICENSE                         # Project license (Unlicense)
├── README.md                       # This file
├── CHANGES.md                      # Changelog and improvements log
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # Environment configuration & validation
│
├── core/
│   ├── __init__.py
│   ├── http.py                     # HTTP client wrapper (Arr services)
│   └── logging.py                  # Structured logging configuration
│
├── services/
│   ├── __init__.py
│   ├── radarr.py                   # Radarr API service wrapper
│   ├── sonarr.py                   # Sonarr API service wrapper
│   └── prowlarr.py                 # Prowlarr API service wrapper
│
├── agents/
│   ├── __init__.py
│   ├── indexer_health_agent.py     # Health monitoring agent (read-only)
│   ├── indexer_control_agent.py    # Control primitives (enable/disable)
│   └── indexer_autoheal_agent.py   # Auto-healing agent (main logic)
│
├── db/
│   ├── __init__.py
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── session.py                  # Database session & initialization
│   └── app.db                      # SQLite database (auto-generated)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration & fixtures
│   ├── test_main.py                # Application tests
│   ├── test_agents.py              # Agent tests
│   ├── test_services.py            # Service layer tests
│   └── test_http.py                # HTTP client tests
│
└── __pycache__/                    # Python bytecode (auto-generated)
```

---

## Development & Testing

### Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=agents --cov=services --cov=core tests/
```

### Code Quality Tools

```bash
# Code formatting
black .

# Linting
ruff check .

# Type hints
mypy agents/ services/ config/ core/ db/

# All checks
black . && ruff check . && mypy agents/ services/ config/ core/ db/
```

### Development Mode

For development with auto-reload:

```bash
uvicorn main:app --reload --log-level debug
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'config'"

**Solution:** Install package in development mode:
```bash
pip install -e .
```

### "Failed to fetch Radarr indexers: Connection refused"

**Solution:** Ensure:
1. Radarr instance is running: `curl http://radarr:7878/api/v3/system/status`
2. Network connectivity: `ping radarr` (or your Radarr hostname/IP)
3. Firewall allows connection to port 7878
4. URL in `.env` is correct

### "No indexers being tested"

**Checklist:**
1. ✓ `.env` file exists with correct URLs and API keys
2. ✓ API keys are valid (not placeholder values)
3. ✓ Services are accessible
4. ✓ Database initialized (should happen automatically)
5. ✓ Check logs for errors: `grep -i error application.log`

### "Scheduler not running"

**Solution:** Ensure app started without errors:
```bash
# Check for startup errors
uvicorn main:app

# In production, use proper ASGI server
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app
```

### Database file too large

**Solution:** Archive old data:
```sql
DELETE FROM indexer_health 
WHERE timestamp < datetime('now', '-90 days');
```

### Disabling indexers too aggressively

**Solution:** Adjust health check schedules or disable auto-heal temporarily:
- Edit schedule intervals in [main.py](main.py)
- Or temporarily set `enable=True` on indexers via Radarr/Sonarr UI

---

## Extending the System

### Adding a Custom Agent

1. Create `agents/custom_agent.py`:
```python
from loguru import logger

class CustomAgent:
    def __init__(self, radarr, sonarr):
        self.radarr = radarr
        self.sonarr = sonarr
        logger.info("Initialized CustomAgent")
    
    async def run(self):
        """Custom logic runs here periodically."""
        logger.info("CustomAgent executing")
        # Your logic here
```

2. Wire up in [main.py](main.py):
```python
from agents.custom_agent import CustomAgent

# In lifespan()...
custom_agent = CustomAgent(radarr, sonarr)
scheduler.add_job(custom_agent.run, "interval", hours=1, id="custom_agent")
```

### Adding a New Service

1. Create `services/new_service.py` with service class
2. Initialize in [main.py](main.py)
3. Pass to agents that need it

---

## Best Practices

### Security
- ✓ Never commit `.env` to version control
- ✓ Use strong API keys (generate new ones if exposed)
- ✓ Restrict API key scopes to indexer management only (if supported)
- ✓ Use HTTPS URLs in production if available

### Operations
- ✓ Monitor logs regularly for unusual patterns
- ✓ Backup database periodically: `cp db/app.db db/app.db.backup-$(date +%Y%m%d)`
- ✓ Test configuration changes in development first
- ✓ Review disabled indexers periodically to understand failure patterns

### Production Deployment
- ✗ **Never** run with `DEBUG=True` in production
- ✗ **Never** use `--reload` flag in production
- ✓ Use production ASGI server (gunicorn, uvicorn, etc.)
- ✓ Configure log rotation to prevent disk full
- ✓ Monitor application health endpoint
- ✓ Set up alerting for critical errors
- ✓ Consider PostgreSQL instead of SQLite for multi-instance deployments

### Performance
- Health checks are lightweight (read-only)
- Auto-heal runs less frequently to avoid excessive API load
- Database uses indexes for fast queries
- All network operations are non-blocking (async)

---

## Upgrading

### From v0.2.0 to v0.3.0+

- New configuration validation at startup
- Enhanced logging with file rotation support
- Database schema unchanged (backward compatible)
- New API endpoints for monitoring
- All existing functionality preserved

---

## License

This project is released into the public domain under the [Unlicense](LICENSE).

---

## Contributing

Contributions are welcome! Please:

1. **Code Style**: Follow PEP 8 (use `black` and `ruff`)
2. **Type Hints**: Add type annotations for all functions
3. **Documentation**: Update docstrings and README
4. **Tests**: Add tests for new features
5. **Commit Messages**: Use clear, descriptive messages

### Making Changes

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, run tests
pytest tests/

# Format and lint
black . && ruff check .

# Commit and push
git add -A
git commit -m "Add my feature"
git push origin feature/my-feature
```

---

## Support & Issues

For questions, bugs, or feature requests:

1. Check [Troubleshooting](#troubleshooting) section first
2. Search existing [GitHub issues](https://github.com/yourusername/ai_arr_control/issues)
3. Open a [new issue](https://github.com/yourusername/ai_arr_control/issues/new) with:
   - Clear description of problem/request
   - Steps to reproduce (if bug)
   - Python version, OS, deployment method
   - Relevant logs (sanitize API keys!)

---

## Version History

### v0.3.0 (Latest)
- **Enhanced Configuration**: Added validation, improved documentation
- **Improved Logging**: Structured logging with file rotation support
- **Better Error Handling**: Comprehensive error handling across all modules
- **Extended Documentation**: Production-grade README with examples
- **Code Quality**: Enhanced docstrings, type hints, inline comments

### v0.2.0
- Initial public release
- Basic health monitoring and auto-heal functionality

---

**Built with ❤️ using FastAPI, SQLAlchemy, and Python 3.11+**
