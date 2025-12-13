# AI Arr Control

**Autonomous AI agent platform for intelligent indexer management and health monitoring in Radarr, Sonarr, and Prowlarr.**

AI Arr Control is a production-ready system that automatically monitors media indexer health across your Radarr and Sonarr installations, tests connectivity, and intelligently disables broken indexers to prevent stalled downloads and search failures.

## Features

- **Autonomous Health Monitoring**: Periodic health checks of all configured indexers
- **Automated Healing**: Automatically disables failing indexers to prevent service degradation
- **Event Logging**: Detailed activity logging with timestamps and error tracking
- **Database History**: Stores all health check results for auditing and trend analysis
- **FastAPI-based**: Lightweight, async-first architecture with built-in `/health` endpoint
- **Extensible Agent Framework**: Clean design allowing custom agents and control strategies
- **Production-Ready**: Error handling, graceful shutdown, proper resource management

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│               FastAPI Application                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │  IndexerHealthAgent (every 30 min)               │   │
│  │  - Tests all indexers in Radarr & Sonarr        │   │
│  │  - Logs results                                  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  IndexerAutoHealAgent (every 2 hours)            │   │
│  │  - Tests indexers & stores results in DB        │   │
│  │  - Disables failing indexers automatically      │   │
│  │  - Controlled by IndexerControlAgent            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         ↓                ↓                ↓
    ┌────────┐      ┌────────┐      ┌─────────┐
    │ Radarr │      │ Sonarr │      │Prowlarr │
    └────────┘      └────────┘      └─────────┘
```

**Components:**
- **IndexerHealthAgent**: Quick health checks without side effects (read-only)
- **IndexerAutoHealAgent**: Comprehensive testing with database recording and automatic remediation
- **IndexerControlAgent**: Low-level primitives for enabling/disabling indexers
- **Services**: HTTP wrappers (Radarr, Sonarr, Prowlarr) with consistent API
- **Database**: SQLite with health check history for reporting and analysis

## Quick Start

### Prerequisites

- Python 3.11+
- Radarr and/or Sonarr instances with API keys
- Optional: Prowlarr instance with API key

### Installation

1. **Clone and setup environment:**
   ```bash
   git clone <repository>
   cd ai_arr_control
   
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your service URLs and API keys
   ```

4. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`. Health check endpoint: `http://localhost:8000/health`

## Configuration

All configuration is loaded from environment variables or a `.env` file.

### Required Variables

```env
RADARR_URL=http://radarr:7878
RADARR_API_KEY=your_api_key_here

SONARR_URL=http://sonarr:8989
SONARR_API_KEY=your_api_key_here

PROWLARR_URL=http://prowlarr:9696
PROWLARR_API_KEY=your_api_key_here
```

### Optional Variables

```env
DEBUG=False                  # Enable debug logging
APP_NAME=AI Arr Control      # Custom app name (default)

# Database URL (defaults to SQLite in db/app.db)
DATABASE_URL=sqlite+aiosqlite:///./db/app.db
```

See `.env.example` for all available options with descriptions.

## Usage

### Health Endpoint

Check if the application and scheduler are running:

```bash
curl http://localhost:8000/health
# Output: {"status":"ok"}
```

### Accessing the Database

Health check history is stored in `db/app.db`. Query recent results:

```python
import sqlite3

conn = sqlite3.connect('db/app.db')
cursor = conn.cursor()

# Get the last 10 health checks for Radarr
cursor.execute("""
  SELECT service, name, success, error, timestamp 
  FROM indexer_health 
  WHERE service = 'radarr' 
  ORDER BY timestamp DESC 
  LIMIT 10
""")

for row in cursor.fetchall():
    print(row)
```

### Logs

The application outputs structured logs to stdout. Examples:

```
INFO     | __main__:startup_event:52 - Initializing database...
INFO     | agents.indexer_health_agent:run:26 - Checking Radarr indexers
INFO     | agents.indexer_health_agent:run:33 - Radarr indexer OK: NZBGeek
WARNING  | agents.indexer_autoheal_agent:run:58 - Indexer radarr/Broken disabled due to failure
ERROR    | agents.indexer_autoheal_agent:run:71 - Failed to fetch sonarr indexers: ConnectionError
```

## Scheduling

The following agents run on automatic schedules:

| Agent | Interval | Purpose |
|-------|----------|---------|
| `IndexerHealthAgent` | 30 minutes | Read-only health check of all indexers |
| `IndexerAutoHealAgent` | 2 hours | Test, record, and disable failing indexers |

To adjust schedules, edit [main.py](main.py).

## Project Structure

```
ai_arr_control/
├── main.py                     # FastAPI app & scheduler setup
├── config/
│   └── settings.py             # Environment configuration
├── core/
│   ├── http.py                 # HTTP client wrapper
│   └── logging.py              # Logging configuration
├── services/
│   ├── radarr.py               # Radarr API wrapper
│   ├── sonarr.py               # Sonarr API wrapper
│   └── prowlarr.py             # Prowlarr API wrapper
├── agents/
│   ├── indexer_health_agent.py        # Health check agent
│   ├── indexer_control_agent.py       # Control primitives
│   └── indexer_autoheal_agent.py      # Auto-healing agent
├── db/
│   ├── models.py               # SQLAlchemy ORM models
│   ├── session.py              # Database session & init
│   └── app.db                  # SQLite database (generated)
├── tests/                      # Test suite (see Testing)
├── .env.example                # Configuration template
├── .gitignore                  # Git exclusions
├── pyproject.toml              # Package metadata & dependencies
└── README.md                   # This file
```

## Development & Testing

### Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type hints
mypy agents/ services/ config/ core/ db/
```

## Troubleshooting

### "ModuleNotFoundError" when running the app

Ensure you've installed the package in development mode:

```bash
pip install -e .
```

### No indexers being tested

1. Verify `.env` file exists with correct service URLs and API keys
2. Check that Radarr/Sonarr instances are accessible: `curl http://radarr:7878/api/v3/system/status`
3. Check logs for connection errors
4. Verify API keys are correct in Radarr/Sonarr UI

### Database file growing large

The `indexer_health` table stores all test results. Optionally clean up old records:

```sql
DELETE FROM indexer_health 
WHERE timestamp < datetime('now', '-30 days');
```

### Scheduler not running

Check that the app started without errors. If using `--reload` in development, the scheduler may restart. For production, use a proper ASGI server:

```bash
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app
```

### "Connection refused" errors

Ensure services (Radarr, Sonarr) are:
- Running and accessible at configured URLs
- Have network connectivity to the AI Arr Control host
- Have API keys correctly configured

## Extending the System

### Adding a New Agent

1. Create a new file in `agents/`
2. Implement the agent class with `async def run()`
3. Wire up in [main.py](main.py) startup event

Example:

```python
class CustomAgent:
    def __init__(self, radarr, sonarr):
        self.radarr = radarr
        self.sonarr = sonarr
    
    async def run(self):
        logger.info("Custom agent running")
        # Your logic here
```

### Adding a New Service

1. Create a new file in `services/`
2. Implement methods matching the Arr API you're wrapping
3. Instantiate in [main.py](main.py) and pass to agents

## Best Practices

1. **Never run with `DEBUG=True` in production**
2. **Use strong API keys** with limited scopes if available
3. **Monitor logs** for unusual patterns or errors
4. **Backup the database** periodically: `cp db/app.db db/app.db.backup`
5. **Test configuration** in a development environment first
6. **Use proper ASGI servers** (gunicorn, uvicorn) in production, not `--reload`

## Performance Considerations

- Health checks are read-only and lightweight
- Auto-heal runs less frequently to avoid excessive API calls
- Database uses SQLite (suitable for single-instance deployments)
- For high-scale deployments, consider PostgreSQL + multiple workers

## License

See [LICENSE](LICENSE) file.

## Contributing

Contributions welcome. Please:
1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass before submitting

## Support

For issues, questions, or feature requests, please open an issue on the repository.
