## Build, Test & Validation Guide

Complete guide for building, testing, and validating the AI Arr Control project.

---

## Prerequisites

- Python 3.11+ (3.12 or 3.13 recommended)
- pip (Python package manager)
- git
- Virtual environment tool (venv or poetry)

---

## Build & Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-username/ai_arr_control.git
cd ai_arr_control
```

### 2. Create Virtual Environment

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Development install with test dependencies
pip install -e ".[dev]"

# Production install (without tests)
pip install -e .

# Verify installation
pip list | grep -E "fastapi|sqlalchemy|pydantic"
```

### 4. Install Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

---

## Configuration

### Create `.env` File

```bash
cp .env.example .env

# Edit with your values
nano .env
```

Required settings:
```env
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_key
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_key
PROWLARR_URL=http://localhost:9696
PROWLARR_API_KEY=your_key
```

### Validate Configuration

```bash
# Python will validate on startup
python -c "from config.settings import settings; print('✓ Config valid')"

# Or run the app and check startup status
python -m uvicorn main:app --host 127.0.0.1 --port 8000
# Visit http://localhost:8000/startup-status
```

---

## Running the Application

### Development Mode (with auto-reload)

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Access at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Production Mode

```bash
# Single process
uvicorn main:app --host 0.0.0.0 --port 8000

# With gunicorn (multiple workers)
pip install gunicorn
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Using CLI

```bash
# Ensure package is installed in editable mode
pip install -e .

# Run commands
ai-arr-control run --host 0.0.0.0 --port 8000
ai-arr-control run --reload  # Development
ai-arr-control check  # Smoke test
ai-arr-control status  # Check if running
ai-arr-control stop  # Stop detached server
```

---

## Testing

### Run All Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=agents --cov=services --cov=config --cov=core --cov=db

# Without coverage
pytest tests/ -v

# Specific test file
pytest tests/test_main.py -v

# Specific test class
pytest tests/test_main.py::TestHealthEndpoint -v

# Specific test
pytest tests/test_main.py::TestHealthEndpoint::test_health_endpoint -v
```

### Run Tests with Output

```bash
# Show print statements and logs
pytest tests/ -v -s

# Show one at a time (slower, better debugging)
pytest tests/ -v -x
```

### Run Integration Tests

```bash
pytest tests/test_integration.py -v
```

### Run Agent Tests

```bash
pytest tests/test_agents.py -v
```

### Code Coverage Report

```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## Code Quality

### Format Code

```bash
# Format with black
black .

# Check without modifying
black --check .
```

### Lint Code

```bash
# Check with ruff
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Check specific file
ruff check services/radarr.py
```

### Type Checking

```bash
# Type check with mypy
mypy agents/ services/ config/ core/ db/

# Strict mode
mypy --strict agents/ services/

# Specific file
mypy agents/base.py
```

### All Quality Checks

```bash
#!/bin/bash
set -e

echo "🔍 Running all quality checks..."

echo "  1. Formatting..."
black --check .

echo "  2. Linting..."
ruff check .

echo "  3. Type checking..."
mypy agents/ services/ config/ core/ db/ 2>/dev/null || true

echo "  4. Running tests..."
pytest tests/ -q

echo "✅ All checks passed!"
```

Save as `scripts/check_all.sh` and run with:
```bash
chmod +x scripts/check_all.sh
./scripts/check_all.sh
```

---

## Validation

### Pre-Commit Checks

```bash
# Run pre-commit on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

### Startup Validation

```bash
# 1. Start the app
python -m uvicorn main:app

# 2. In another terminal, check startup
curl http://localhost:8000/startup-status | jq

# Expected:
# {
#   "complete": true,
#   "agents_initialized": true,
#   ...
# }
```

### Health Check Validation

```bash
# Health endpoint
curl http://localhost:8000/health

# Should return:
# {"status":"ok","service":"AI Arr Control"}

# Root endpoint
curl http://localhost:8000/ | jq .

# Should have service info and endpoints
```

### Configuration Validation

```bash
# Test configuration before running
python << 'EOF'
from config.settings import settings

# This will raise if config is invalid
settings.validate_at_startup()
print("✓ Configuration is valid")
EOF
```

### Database Validation

```bash
# Check database connection
python << 'EOF'
import asyncio
from db.session import engine

async def test_db():
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")
        print("✓ Database is accessible")

asyncio.run(test_db())
EOF
```

### Service Connectivity Validation

```bash
# Test all services
python << 'EOF'
import asyncio
from core.validator import ConfigurationValidator

async def validate():
    validator = ConfigurationValidator()
    success, errors, warnings = await validator.validate_all()
    
    if success:
        print("✓ All services are reachable")
    else:
        print("✗ Configuration errors:")
        for error in errors:
            print(f"  - {error}")

asyncio.run(validate())
EOF
```

---

## Docker Build & Test

### Build Docker Image

```bash
# Build locally
docker build -t ai-arr-control:latest .

# Build with custom tag
docker build -t ai-arr-control:v0.4.0 .

# Build with buildkit for better caching
DOCKER_BUILDKIT=1 docker build -t ai-arr-control:latest .
```

### Test Docker Image

```bash
# Run container with env file
docker run --env-file .env \
  -p 8000:8000 \
  -v ./db:/app/db \
  ai-arr-control:latest

# Run with interactive terminal
docker run -it --env-file .env \
  -p 8000:8000 \
  ai-arr-control:latest /bin/bash

# Run specific command
docker run --env-file .env \
  ai-arr-control:latest \
  python -m pytest tests/ -v
```

### Docker Compose Test

```bash
# Start stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ai-arr-control

# Run tests
docker-compose exec ai-arr-control pytest tests/ -v

# Stop stack
docker-compose down
```

---

## Smoke Tests

Quick validation that everything works:

```bash
# 1. Start app in background
python -m uvicorn main:app &
sleep 2

# 2. Test health endpoint
curl -f http://localhost:8000/health || exit 1

# 3. Test API documentation
curl -f http://localhost:8000/docs > /dev/null || exit 1

# 4. Test indexer endpoint
curl -f http://localhost:8000/indexers > /dev/null || exit 1

# 5. Stop app
pkill -f uvicorn

echo "✓ All smoke tests passed"
```

Or use the built-in CLI:

```bash
python -m tools.cli check
```

---

## Performance Testing

### Load Testing (with Apache Bench)

```bash
# Install ab
brew install httpd  # macOS
sudo apt-get install apache2-utils  # Linux

# Test health endpoint
ab -n 100 -c 10 http://localhost:8000/health

# Test indexers endpoint
ab -n 50 -c 5 http://localhost:8000/indexers
```

### Load Testing (with vegeta)

```bash
# Install vegeta
go get -u github.com/tsenart/vegeta

# Create targets file
cat > targets.txt << EOF
GET http://localhost:8000/health
GET http://localhost:8000/indexers
GET http://localhost:8000/agents/status
EOF

# Run load test
vegeta attack -duration=30s -rate=10 < targets.txt | vegeta report
```

---

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Format check
        run: black --check .
      
      - name: Lint
        run: ruff check .
      
      - name: Type check
        run: mypy agents/ services/ config/ core/ db/
      
      - name: Run tests
        run: pytest tests/ -v
```

---

## Release Validation

Before releasing a new version:

```bash
#!/bin/bash
set -e

echo "🔍 Pre-release validation..."

# 1. Check all tests pass
echo "  Running tests..."
pytest tests/ -q

# 2. Check code quality
echo "  Checking code quality..."
black --check .
ruff check .

# 3. Check type safety
echo "  Type checking..."
mypy agents/ services/ config/ core/ db/ 2>/dev/null || true

# 4. Build package
echo "  Building package..."
python -m build

# 5. Check metadata
echo "  Validating package..."
twine check dist/*

echo "✅ All pre-release checks passed!"
echo ""
echo "Next steps:"
echo "  1. Update CHANGELOG.md"
echo "  2. Update version in pyproject.toml"
echo "  3. git tag -a v0.x.x -m 'Release v0.x.x'"
echo "  4. git push --tags"
echo "  5. twine upload dist/*"
```

---

## Troubleshooting Build Issues

### Import Errors

```bash
# Ensure package is installed in editable mode
pip install -e .

# Or add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -e ".[dev]" --force-reinstall --no-cache-dir
```

### Pytest Discovery Issues

```bash
# Explicitly specify test directory
pytest tests/

# Or with path
python -m pytest tests/ -v
```

### Database Lock (SQLite)

```bash
# Stop application and remove lock files
rm db/app.db-journal db/app.db-shm db/app.db-wal 2>/dev/null || true

# Restart
python -m uvicorn main:app
```
