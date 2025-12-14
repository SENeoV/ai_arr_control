## Troubleshooting Guide

Solutions for common issues and how to debug problems.

---

## Startup Issues

### Configuration Validation Failed

**Problem**: Application exits with "Configuration validation failed"

**Solutions**:
1. Ensure all required environment variables are set:
   ```bash
   # Check your .env file has these
   RADARR_URL=
   RADARR_API_KEY=
   SONARR_URL=
   SONARR_API_KEY=
   PROWLARR_URL=
   PROWLARR_API_KEY=
   ```

2. Verify URLs are correctly formatted (include http:// or https://):
   ```bash
   # Wrong
   RADARR_URL=radarr:7878
   # Correct
   RADARR_URL=http://radarr:7878
   ```

3. Check that API keys are valid (not placeholder values):
   ```bash
   # Wrong
   RADARR_API_KEY=your_radarr_api_key_here
   # Correct
   RADARR_API_KEY=abc123def456ghi789jkl012mnopqrs
   ```

4. Enable debug mode to see more details:
   ```bash
   DEBUG=true
   ```

---

### Database Initialization Failed

**Problem**: "Database initialization failed"

**Cause**: Cannot connect to or create database

**Solutions**:

**For SQLite**:
```bash
# Ensure db/ directory exists and is writable
mkdir -p db
chmod 755 db

# Check database file path
ls -la db/app.db  # Should exist or directory should exist for creation

# Delete corrupted database
rm db/app.db  # Will be recreated on startup
```

**For PostgreSQL**:
```bash
# 1. Verify PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

# 2. Create database manually
createdb ai_arr_control

# 3. Verify connection string
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_arr_control

# 4. Test connection with psql
psql -U user -d ai_arr_control -c "SELECT 1"
```

**For MySQL**:
```bash
# 1. Create database manually
mysql -u root -p -e "CREATE DATABASE ai_arr_control;"

# 2. Grant permissions
mysql -u root -p -e "GRANT ALL ON ai_arr_control.* TO 'ai_arr_user'@'localhost';"

# 3. Verify connection
mysql -u ai_arr_user -p ai_arr_control -e "SELECT 1"
```

---

### Cannot Connect to Services

**Problem**: "Cannot connect to Radarr/Sonarr/Prowlarr"

**Solutions**:

1. **Verify services are running**:
   ```bash
   # Test endpoint directly
   curl http://localhost:7878/api/v3/system/status
   curl http://localhost:8989/api/v3/system/status
   curl http://localhost:9696/api/v1/system/status
   ```

2. **Check firewall/network**:
   ```bash
   # Test from application host
   ping radarr  # If using hostnames
   nc -zv localhost 7878  # Check if port is listening
   ```

3. **Verify API keys are correct**:
   - Go to each application's Settings → General → Security
   - Copy the exact API key into .env
   - Restart application

4. **Check for auth/SSL issues**:
   ```bash
   # If using HTTPS, verify certificate
   curl -k https://radarr:7878/api/v3/system/status
   
   # Add -H for API key if needed
   curl -H "X-Api-Key: your_key" https://radarr:7878/api/v3/system/status
   ```

---

## Runtime Issues

### Health Check Failing

**Problem**: Indexers report as unhealthy when they should be working

**Solutions**:

1. **Manual indexer test**:
   ```bash
   # Test specific indexer through API
   curl -X POST http://localhost:8000/indexers/radarr/1/test
   ```

2. **Check application logs**:
   ```bash
   # View logs
   tail -f ai_arr_control.log
   
   # Or with docker
   docker logs -f ai_arr_control
   ```

3. **Check Radarr/Sonarr logs**:
   - Radarr: Settings → System → Logs
   - Sonarr: Settings → System → Logs
   - Look for connection errors or timeouts

4. **Test indexer directly in Radarr/Sonarr**:
   - Go to Settings → Indexers
   - Click test icon next to indexer
   - Check if it passes/fails

---

### Agents Not Running

**Problem**: "Health check cycle not running" or stuck

**Solutions**:

1. **Check scheduler status**:
   ```bash
   curl http://localhost:8000/agents/status | jq .scheduler
   ```

2. **Manually trigger agent**:
   ```bash
   curl -X POST http://localhost:8000/agents/health/run
   ```

3. **Check if agent is disabled**:
   - Look at /agents/status response
   - Check `"enabled": true` for each agent

4. **View startup status**:
   ```bash
   curl http://localhost:8000/startup-status
   ```

5. **Look for stuck processes**:
   ```bash
   # Check if uvicorn is still running
   ps aux | grep uvicorn
   
   # Kill and restart if stuck
   pkill -f uvicorn
   python -m uvicorn main:app --reload
   ```

---

### Memory Usage Growing

**Problem**: Application memory usage increases over time

**Causes & Solutions**:

1. **Event log growing indefinitely**:
   ```bash
   # Check event log file size
   du -sh logs/events.jsonl
   
   # If too large, rotate/archive
   mv logs/events.jsonl logs/events.jsonl.old
   gzip logs/events.jsonl.old
   ```

2. **Database queries holding connections**:
   ```bash
   # Restart application to reset connections
   kill $(pgrep -f uvicorn)
   python -m uvicorn main:app
   ```

3. **Cache growing too large** (if enabled):
   - Default cache has LRU eviction
   - Reduce `HEALTH_CHECK_CACHE_MAX_ENTRIES` if needed

---

## Performance Issues

### Slow API Responses

**Problem**: Endpoints taking > 5 seconds to respond

**Solutions**:

1. **Check database size**:
   ```bash
   # For SQLite
   ls -lh db/app.db
   
   # If large (>100MB), consider archiving old records
   sqlite3 db/app.db "DELETE FROM indexer_health WHERE timestamp < datetime('now', '-30 days')"
   ```

2. **Check service responsiveness**:
   ```bash
   # Test external services directly
   time curl http://radarr:7878/api/v3/indexer
   
   # If slow, issue is with service, not AI Arr Control
   ```

3. **Enable response caching**:
   ```bash
   # In config if cache feature is integrated
   HEALTH_CHECK_CACHE_TTL_SECONDS=600  # 10 minutes
   ```

4. **Check database connection pool**:
   ```python
   # For PostgreSQL/MySQL, adjust in config
   SQLALCHEMY_POOL_SIZE=10
   SQLALCHEMY_MAX_OVERFLOW=20
   ```

---

## Indexer Management Issues

### Indexers Being Disabled Unexpectedly

**Problem**: Healthy indexers are being disabled by autoheal

**Solutions**:

1. **Check autoheal logic**:
   ```bash
   # Run health check manually
   curl -X POST http://localhost:8000/agents/health/run
   
   # Check results in database
   curl http://localhost:8000/health-history?hours=1
   ```

2. **Disable autoheal temporarily**:
   ```bash
   # Restart app or use API to disable agent
   # (would need to implement agent enable/disable endpoint)
   ```

3. **Check indexer timeout settings**:
   - If indexers are slow, increase timeout
   - Currently hardcoded to 30 seconds
   - May need to parameterize

---

### Cannot Re-enable Disabled Indexer

**Problem**: Enable endpoint returns success but indexer stays disabled

**Solutions**:

1. **Check if indexer has auth issues**:
   - Test the indexer in Radarr/Sonarr directly
   - If it fails there, fix the indexer config first

2. **Manually enable in Radarr/Sonarr**:
   - Settings → Indexers → toggle Enable checkbox
   - Verify it works

3. **Check for API issues**:
   ```bash
   # Verify update is reaching Radarr
   curl -X PUT http://localhost:7878/api/v3/indexer/1 \
     -H "X-Api-Key: key" \
     -H "Content-Type: application/json" \
     -d '{"id":1,"enable":true}'
   ```

---

## Docker Issues

### Container Keeps Restarting

**Problem**: Docker container exits immediately or keeps restarting

**Solutions**:

1. **Check logs**:
   ```bash
   docker logs ai-arr-control
   docker logs --tail=50 ai-arr-control
   ```

2. **Verify environment variables**:
   ```bash
   docker run --env-file .env ai-arr-control env | grep RADARR
   ```

3. **Check file permissions**:
   ```bash
   # db/ directory must be writable
   docker run -v ./db:/app/db -v ./logs:/app/logs ai-arr-control
   ```

4. **Run interactively for debugging**:
   ```bash
   docker run -it \
     --env-file .env \
     -p 8000:8000 \
     ai-arr-control /bin/bash
   
   # Then manually run
   python main.py
   ```

---

### Port Already in Use

**Problem**: "Address already in use" or "Port 8000 is in use"

**Solutions**:

```bash
# Find process using port 8000
lsof -i :8000

# Kill it (be careful!)
kill -9 <PID>

# Or use different port
docker run -p 8001:8000 ai-arr-control

# Or change in docker-compose.yml
ports:
  - "8001:8000"
```

---

## Database Issues

### "Disk I/O error" (SQLite)

**Problem**: Database locked or I/O error

**Solutions**:

```bash
# 1. Stop application
kill $(pgrep -f uvicorn)

# 2. Check/repair database
sqlite3 db/app.db "PRAGMA integrity_check"

# 3. If corrupted, backup and delete
cp db/app.db db/app.db.backup
rm db/app.db

# 4. Restart - will recreate
python -m uvicorn main:app
```

---

### PostgreSQL: "too many connections"

**Problem**: Pool exhausted, cannot get connection

**Solutions**:

```bash
# 1. Check connections
psql -U postgres -d ai_arr_control -c "SELECT count(*) FROM pg_stat_activity;"

# 2. Kill idle connections
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# 3. Restart application to reset pool
```

---

## Network/Connectivity

### Firewall Blocking Connections

**Problem**: Services not reachable even though they're running

**Solutions**:

```bash
# Check firewall rules
sudo iptables -L | grep 7878
sudo firewall-cmd --list-all

# Temporarily disable firewall for testing
sudo systemctl stop firewalld

# Or allow specific port
sudo firewall-cmd --permanent --add-port=7878/tcp
sudo firewall-cmd --reload
```

---

## Performance Tuning

### Reduce Health Check Frequency

Change in main.py or via environment variable (if implemented):

```python
# Currently hardcoded to 30 minutes
# Consider parameterizing as HEALTH_CHECK_INTERVAL_MINUTES=60
orchestrator.register_agent(health_agent, interval_seconds=60 * 60)
```

### Enable Response Caching

```env
# Cache health checks for 10 minutes to reduce API calls
HEALTH_CHECK_CACHE_TTL_SECONDS=600
```

---

## Getting Help

If your issue isn't listed here:

1. **Enable debug mode** and capture logs:
   ```bash
   DEBUG=true
   # Run again, capture output
   ```

2. **Check health endpoints**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/agents/status
   ```

3. **Review startup status**:
   ```bash
   curl http://localhost:8000/startup-status | jq
   ```

4. **Check recent events**:
   ```bash
   curl http://localhost:8000/events | jq
   ```

5. **Report issue** with:
   - AI Arr Control version
   - Python version (`python --version`)
   - OS/platform
   - Relevant log output (with sensitive info redacted)
   - Steps to reproduce
