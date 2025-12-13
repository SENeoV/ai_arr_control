# Installation & Testing Guide

Quick reference for setting up and testing AI Arr Control.

## Prerequisites

- Python 3.11 or later
- pip (Python package manager)
- git (for cloning)
- Radarr, Sonarr, Prowlarr instances running

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/ai_arr_control.git
cd ai_arr_control
```

### 2. Create Virtual Environment

```bash
# On macOS/Linux
python3.11 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
pip list | grep -E "fastapi|uvicorn|pydantic|sqlalchemy"
```

### 4. Configure Environment

```bash
# Copy configuration template
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

**Required settings:**
```env
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_api_key_here
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_api_key_here
PROWLARR_URL=http://localhost:9696
PROWLARR_API_KEY=your_api_key_here
```

### 5. Initialize Database

The database is auto-created on first run, but you can initialize manually:

```bash
python -c "
from db.session import init_db
import asyncio

asyncio.run(init_db())
print('✓ Database initialized')
"
```

## Running the Application

### Development Mode

```bash
# Start with auto-reload for development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Application will restart when you edit files
# Access at http://localhost:8000
```

### Production Mode

```bash
# Use production ASGI server
pip install gunicorn

gunicorn -w 1 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  main:app
```

### Docker

```bash
# Build image
docker build -t ai-arr-control:latest .

# Run container
docker run -d \
  --name ai-arr-control \
  -p 8000:8000 \
  -v ./db:/app/db \
  -e RADARR_URL=http://radarr:7878 \
  -e RADARR_API_KEY=key \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=key \
  -e PROWLARR_URL=http://prowlarr:9696 \
  -e PROWLARR_API_KEY=key \
  ai-arr-control:latest

# View logs
docker logs -f ai-arr-control
```

## Testing

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_agents.py -v
pytest tests/test_services.py -v
pytest tests/test_http.py -v
```

### Run with Coverage Report

```bash
pytest tests/ --cov=agents --cov=services --cov=core --cov=db

# Generate HTML coverage report
pytest tests/ --cov=agents --cov=services --cov=core --cov=db \
  --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run with Verbose Output

```bash
pytest tests/ -v -s

# -v: verbose
# -s: show print statements
```

### Run Tests in Watch Mode

```bash
pip install pytest-watch

ptw tests/
```

## Code Quality

### Code Formatting

```bash
# Format code with black
black .

# Check formatting without modifying
black --check .
```

### Linting

```bash
# Check for errors and style issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Type Checking

```bash
# Check type hints
mypy agents/ services/ config/ core/ db/

# Strict mode
mypy --strict agents/
```

### Run All Quality Checks

```bash
# Script to run all checks
#!/bin/bash
set -e
echo "Checking code formatting..."
black --check .
echo "Linting..."
ruff check .
echo "Type checking..."
mypy agents/ services/ config/ core/ db/
echo "Running tests..."
pytest tests/
echo "✓ All checks passed!"
```

## Verification Checklist

After installation, verify everything works:

```bash
# 1. Check imports
python -c "from main import app; print('✓ Main app imports')"
python -c "from config.settings import settings; print('✓ Settings import')"

# 2. Check configuration loads
python -c "from config.settings import settings; print(f'✓ App: {settings.app_name}')"

# 3. Check database can be created
python -c "from db.models import Base; print('✓ Database models load')"

# 4. Check services load
python -c "from services.radarr import RadarrService; print('✓ Services load')"

# 5. Check agents load
python -c "from agents.indexer_health_agent import IndexerHealthAgent; print('✓ Agents load')"

# 6. Health check endpoint
curl http://localhost:8000/health

# 7. API documentation
curl -s http://localhost:8000/openapi.json | python -m json.tool | head -20
```

## Troubleshooting

### ModuleNotFoundError

```bash
# Reinstall package in development mode
pip install -e ".[dev]"
```

### Configuration Errors

```bash
# Check .env file exists
ls -la .env

# Test configuration loads
python -c "from config.settings import settings; print(settings.dict())"
```

### Database Errors

```bash
# Check database file
ls -la db/app.db

# Reset database (deletes all history)
rm db/app.db
# Database will be recreated on next run
```

### Connection Errors

```bash
# Test connectivity to services
curl http://localhost:7878/api/v3/system/status  # Radarr
curl http://localhost:8989/api/v3/system/status  # Sonarr
curl http://localhost:9696/api/v1/system/status  # Prowlarr

# Test from inside application
python -c "
from core.http import ArrHttpClient
import asyncio

async def test():
    client = ArrHttpClient('http://localhost:7878', 'api_key')
    try:
        result = await client.get('/api/v3/system/status')
        print('✓ Connected to Radarr')
    except Exception as e:
        print(f'✗ Connection failed: {e}')
    finally:
        await client.close()

asyncio.run(test())
"
```

## Environment Variables Reference

### Required

| Variable | Example | Description |
|----------|---------|-------------|
| RADARR_URL | http://radarr:7878 | Radarr service URL |
| RADARR_API_KEY | abc123... | Radarr API key |
| SONARR_URL | http://sonarr:8989 | Sonarr service URL |
| SONARR_API_KEY | def456... | Sonarr API key |
| PROWLARR_URL | http://prowlarr:9696 | Prowlarr service URL |
| PROWLARR_API_KEY | ghi789... | Prowlarr API key |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| APP_NAME | AI Arr Control | Application name |
| DEBUG | false | Enable debug mode |
| DATABASE_URL | sqlite+aiosqlite:///./db/app.db | Database connection URL |

## Next Steps

1. **Run the application**: `uvicorn main:app --reload`
2. **Check the API**: http://localhost:8000/docs
3. **Review logs**: Monitor console output
4. **Test agents**: Let them run through a cycle
5. **Check database**: Query health results
6. **Deploy**: Use Docker or your preferred platform

## Getting Help

- Check [README.md](README.md) for detailed documentation
- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment guides
- Review [CHANGES.md](CHANGES.md) for latest improvements
- Open GitHub issue for bugs/questions
- Check existing issues for common problems

## Quick Commands Reference

```bash
# Development
venv/bin/activate                              # Activate environment
pip install -e ".[dev]"                        # Install with dev tools
uvicorn main:app --reload                      # Run with auto-reload
pytest tests/ -v                               # Run tests verbosely
black . && ruff check . && mypy agents/        # Quality checks

# Production
docker build -t ai-arr-control .               # Build Docker image
docker run -d ... ai-arr-control               # Run container
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app  # Production server

# Database
python -c "from db.session import init_db; asyncio.run(init_db())"  # Init DB
sqlite3 db/app.db "SELECT * FROM indexer_health LIMIT 5;"            # Query DB
```

---

For more detailed information, see [README.md](README.md) and [DEPLOYMENT.md](DEPLOYMENT.md).
