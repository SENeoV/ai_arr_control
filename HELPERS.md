# AI Arr Control - Management Helper Scripts

Quick-start helper scripts to easily manage the AI Arr Control application without memorizing CLI arguments.

## Overview

Two helper scripts are provided:
- **Windows**: `scripts/manage.ps1` (PowerShell)
- **Linux/macOS**: `scripts/manage.sh` (Bash)

Both scripts provide identical functionality for starting, stopping, restarting, and monitoring your AI Arr Control application.

## Quick Start

### Windows (PowerShell)

```powershell
# Start the server
.\scripts\manage.ps1 start

# Start on custom port
.\scripts\manage.ps1 start -Port 9000

# Start in background
.\scripts\manage.ps1 start -DetachMode

# Stop the server
.\scripts\manage.ps1 stop

# Restart the server
.\scripts\manage.ps1 restart

# Check status
.\scripts\manage.ps1 status

# View logs
.\scripts\manage.ps1 logs

# Health check
.\scripts\manage.ps1 health

# View metrics
.\scripts\manage.ps1 metrics

# View events
.\scripts\manage.ps1 events
```

### Linux/macOS (Bash)

```bash
# Make script executable
chmod +x scripts/manage.sh

# Start the server
./scripts/manage.sh start

# Start on custom port
PORT=9000 ./scripts/manage.sh start

# Start in background
DETACH_MODE=true ./scripts/manage.sh start

# Stop the server
./scripts/manage.sh stop

# Restart the server
./scripts/manage.sh restart

# Check status
./scripts/manage.sh status

# View logs
./scripts/manage.sh logs

# Health check
./scripts/manage.sh health

# View metrics
./scripts/manage.sh metrics

# View events
./scripts/manage.sh events
```

## Commands

### `start`
Start the AI Arr Control server.

**Windows:**
```powershell
.\scripts\manage.ps1 start [-Port <int>] [-Host <string>] [-DetachMode]
```

**Linux/macOS:**
```bash
./scripts/manage.sh start [PORT=<int>] [HOST=<string>] [DETACH_MODE=true]
```

**Options:**
- `-Port` / `PORT`: Server port (default: 8000)
- `-Host` / `HOST`: Server host (default: 127.0.0.1)
- `-DetachMode` / `DETACH_MODE=true`: Run server in background

**Examples:**
```powershell
# Windows
.\scripts\manage.ps1 start
.\scripts\manage.ps1 start -Port 9000
.\scripts\manage.ps1 start -DetachMode
```

```bash
# Linux/macOS
./scripts/manage.sh start
PORT=9000 ./scripts/manage.sh start
DETACH_MODE=true ./scripts/manage.sh start
```

### `stop`
Stop the running server.

**Windows:**
```powershell
.\scripts\manage.ps1 stop
```

**Linux/macOS:**
```bash
./scripts/manage.sh stop
```

If the server doesn't stop gracefully, the script will force-kill the process.

### `restart`
Stop and restart the server (useful for applying configuration changes).

**Windows:**
```powershell
.\scripts\manage.ps1 restart
```

**Linux/macOS:**
```bash
./scripts/manage.sh restart
```

### `status`
Check if the server is running and display current statistics.

**Output includes:**
- Server status (running/not running)
- Startup completion status
- Initialized agents (health check, autoheal, discovery)
- Uptime in seconds
- Total operations, successful, and failed counts

**Windows:**
```powershell
.\scripts\manage.ps1 status
```

**Linux/macOS:**
```bash
./scripts/manage.sh status
```

**Example output:**
```
ℹ Checking server status...

✓ Server is RUNNING on http://127.0.0.1:8000
  Status: ok
  Startup Complete: True
  Agents Initialized:
    ✓ Health Check
    ✓ Autoheal
  Uptime: 45 seconds
  Operations: 12 total (10 successful, 2 failed)
```

### `logs`
Display recent application logs.

**Windows:**
```powershell
.\scripts\manage.ps1 logs [-LogLines <int>]
```

**Linux/macOS:**
```bash
./scripts/manage.sh logs [LOG_LINES=<int>]
```

**Options:**
- `-LogLines` / `LOG_LINES`: Number of log lines to show (default: 50)

**Examples:**
```powershell
# Windows
.\scripts\manage.ps1 logs
.\scripts\manage.ps1 logs -LogLines 100
```

```bash
# Linux/macOS
./scripts/manage.sh logs
LOG_LINES=100 ./scripts/manage.sh logs
```

### `health`
Perform a quick health check of all services (Radarr, Sonarr, Prowlarr).

**Output includes:**
- Server health status
- Total indexers per service
- Enabled vs disabled indexers
- Health check success rates

**Windows:**
```powershell
.\scripts\manage.ps1 health
```

**Linux/macOS:**
```bash
./scripts/manage.sh health
```

**Example output:**
```
ℹ Performing health check...

✓ Server Health: ok
✓ Service: AI Arr Control
  Status by Service:
    ✓ RADARR: 8 indexers (7 enabled, 1 disabled)
      Health: 100.0% success rate
    ✓ SONARR: 5 indexers (4 enabled, 1 disabled)
      Health: 96.0% success rate
```

### `metrics`
Display application metrics and uptime information.

**Output includes:**
- Application uptime
- Total operations count
- Successful vs failed operations
- Success rate percentage

**Windows:**
```powershell
.\scripts\manage.ps1 metrics
```

**Linux/macOS:**
```bash
./scripts/manage.sh metrics
```

**Example output:**
```
ℹ Retrieving metrics...

Application Metrics:
  Uptime: 2.45 minutes
  Total Operations: 156
  Successful: 154
  Failed: 2
  Success Rate: 98.72%
```

### `events`
Display recent system events from the audit log.

Shows the 10 most recent events with timestamps, event types, and severity levels.

**Windows:**
```powershell
.\scripts\manage.ps1 events
```

**Linux/macOS:**
```bash
./scripts/manage.sh events
```

### `init-db`
Initialize the application database (creates tables if needed).

**Windows:**
```powershell
.\scripts\manage.ps1 init-db
```

**Linux/macOS:**
```bash
./scripts/manage.sh init-db
```

**When to use:**
- First-time setup
- After deleting the database file
- Recovering from database corruption

### `test`
Run the full test suite.

**Windows:**
```powershell
.\scripts\manage.ps1 test
```

**Linux/macOS:**
```bash
./scripts/manage.sh test
```

Tests cover:
- Service integration with Arr applications
- Agent functionality (health checks, autoheal, discovery)
- API endpoints
- Database operations

### `version`
Display the current application version.

**Windows:**
```powershell
.\scripts\manage.ps1 version
```

**Linux/macOS:**
```bash
./scripts/manage.sh version
```

### `help`
Display help information about all available commands.

**Windows:**
```powershell
.\scripts\manage.ps1 help
```

**Linux/macOS:**
```bash
./scripts/manage.sh help
```

## Common Workflows

### First-Time Setup

```powershell
# Windows
.\scripts\manage.ps1 init-db          # Initialize database
.\scripts\manage.ps1 start             # Start server
.\scripts\manage.ps1 status            # Check status
```

```bash
# Linux/macOS
chmod +x scripts/manage.sh
./scripts/manage.sh init-db           # Initialize database
./scripts/manage.sh start              # Start server
./scripts/manage.sh status             # Check status
```

### Development Workflow

```powershell
# Windows
# Terminal 1: Run server in foreground for easy log viewing
.\scripts\manage.ps1 start

# Terminal 2: Monitor server
.\scripts\manage.ps1 status
.\scripts\manage.ps1 logs
```

```bash
# Linux/macOS
# Terminal 1: Run server in foreground
./scripts/manage.sh start

# Terminal 2: Monitor server
./scripts/manage.sh status
./scripts/manage.sh logs
```

### Production Deployment

```powershell
# Windows
# Start in background and keep running
.\scripts\manage.ps1 start -DetachMode

# Periodically check status
.\scripts\manage.ps1 status

# Monitor health
.\scripts\manage.ps1 health

# View metrics
.\scripts\manage.ps1 metrics
```

```bash
# Linux/macOS
# Start in background
DETACH_MODE=true ./scripts/manage.sh start

# Periodically check status
./scripts/manage.sh status

# Monitor health
./scripts/manage.sh health

# View metrics
./scripts/manage.sh metrics
```

### Troubleshooting

```powershell
# Windows
# 1. Check if server is running
.\scripts\manage.ps1 status

# 2. View recent logs
.\scripts\manage.ps1 logs -LogLines 100

# 3. Run health check
.\scripts\manage.ps1 health

# 4. Restart server
.\scripts\manage.ps1 restart

# 5. Run tests
.\scripts\manage.ps1 test
```

```bash
# Linux/macOS
# 1. Check if server is running
./scripts/manage.sh status

# 2. View recent logs
LOG_LINES=100 ./scripts/manage.sh logs

# 3. Run health check
./scripts/manage.sh health

# 4. Restart server
./scripts/manage.sh restart

# 5. Run tests
./scripts/manage.sh test
```

## Environment Variables

### Windows (PowerShell)

Pass parameters using PowerShell syntax:

```powershell
# Custom port
.\scripts\manage.ps1 start -Port 9000

# Custom host
.\scripts\manage.ps1 start -Host 0.0.0.0

# Detach mode
.\scripts\manage.ps1 start -DetachMode

# Show more logs
.\scripts\manage.ps1 logs -LogLines 200
```

### Linux/macOS (Bash)

Set environment variables before running:

```bash
# Custom port
PORT=9000 ./scripts/manage.sh start

# Custom host
HOST=0.0.0.0 ./scripts/manage.sh start

# Detach mode
DETACH_MODE=true ./scripts/manage.sh start

# Show more logs
LOG_LINES=200 ./scripts/manage.sh logs

# Combine multiple
PORT=9000 DETACH_MODE=true ./scripts/manage.sh start
```

## Output Examples

### Status Check

```
ℹ Checking server status...

✓ Server is RUNNING on http://127.0.0.1:8000
  Status: ok
  Startup Complete: True
  Agents Initialized:
    ✓ Health Check
    ✓ Autoheal
    ✓ Discovery
  Uptime: 234 seconds
  Operations: 45 total (44 successful, 1 failed)
```

### Health Check

```
ℹ Performing health check...

✓ Server Health: ok
✓ Service: AI Arr Control

Service Status:
  ✓ RADARR: 12 indexers (11 enabled, 1 disabled)
    Health: 100.0% success rate
  ✓ SONARR: 8 indexers (7 enabled, 1 disabled)
    Health: 95.5% success rate
  ✓ PROWLARR: 20 indexers (19 enabled, 1 disabled)
    Health: 98.3% success rate
```

### Metrics

```
ℹ Retrieving metrics...

Application Metrics:
  Uptime: 5.67 minutes
  Total Operations: 234
  Successful: 230
  Failed: 4
  Success Rate: 98.29%
```

## Troubleshooting

### "Server is not running" when trying to stop

The script automatically detects if the server isn't running and handles it gracefully. No error handling needed.

### Permission denied on Linux/macOS

Make the script executable:

```bash
chmod +x scripts/manage.sh
```

### Port already in use

Change the port:

```powershell
# Windows
.\scripts\manage.ps1 start -Port 9000
```

```bash
# Linux/macOS
PORT=9000 ./scripts/manage.sh start
```

### Can't connect to server

1. Check if server is running: `.\scripts\manage.ps1 status`
2. Check logs: `.\scripts\manage.ps1 logs`
3. Try restarting: `.\scripts\manage.ps1 restart`
4. Verify configuration in `config/settings.py`

### Tests fail

```powershell
# Windows
.\scripts\manage.ps1 init-db    # Reset database
.\scripts\manage.ps1 test       # Run tests again
```

```bash
# Linux/macOS
./scripts/manage.sh init-db     # Reset database
./scripts/manage.sh test        # Run tests again
```

## Integration with System Services

### Windows: Run as a Service

To run AI Arr Control as a Windows Service:

1. Create a batch file that calls the PowerShell script
2. Use `nssm` (Non-Sucking Service Manager) or `NSSM` to install as service

```powershell
# Using NSSM (install once)
nssm install AiArrControl "C:\path\to\scripts\manage.ps1 start -DetachMode"
nssm start AiArrControl
```

### Linux/macOS: systemd Service

Create `/etc/systemd/system/ai-arr-control.service`:

```ini
[Unit]
Description=AI Arr Control
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ai_arr_control
ExecStart=/path/to/scripts/manage.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl enable ai-arr-control
sudo systemctl start ai-arr-control
sudo systemctl status ai-arr-control
```

## Tips & Best Practices

1. **Use `-DetachMode` / `DETACH_MODE=true` for production** to run in the background
2. **Monitor regularly** with `status` and `health` commands
3. **Check logs** when things aren't working as expected
4. **Keep metrics tracking** enabled for performance insights
5. **Use `restart` after** configuration changes
6. **Run tests periodically** to catch integration issues early

## Additional Resources

- See [README.md](../README.md) for full documentation
- See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) for detailed problem solving
- See [DEPLOYMENT.md](../DEPLOYMENT.md) for production deployment guide
