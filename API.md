## API Reference

Complete documentation of AI Arr Control REST API endpoints, request/response formats, and examples.

### Base URL

```
http://localhost:8000
```

All responses are JSON. Error responses include a `detail` field with error message.

---

## Health & Monitoring

### Health Check

**Endpoint**: `GET /health`

**Description**: Basic health check for load balancers and monitoring.

**Response**:
```json
{
  "status": "ok",
  "service": "AI Arr Control"
}
```

**Status Code**: 200 (always, if service is running)

---

### Service Info

**Endpoint**: `GET /`

**Description**: Get service metadata and available endpoints.

**Response**:
```json
{
  "service": "AI Arr Control",
  "version": "0.4.0",
  "description": "AI-powered autonomous indexer management and health monitoring",
  "endpoints": {
    "monitoring": {
      "health": "/health",
      "stats": "/indexers/stats",
      "health_history": "/health-history",
      "agent_status": "/agents/status"
    },
    "indexers": {
      "list_all": "/indexers",
      "list_by_service": "/indexers/{service}",
      "test_indexer": "POST /indexers/{service}/{indexer_id}/test",
      "disable_indexer": "POST /indexers/{service}/{indexer_id}/disable",
      "enable_indexer": "POST /indexers/{service}/{indexer_id}/enable"
    },
    "agents": {
      "run_health_check": "POST /agents/health/run",
      "run_autoheal": "POST /agents/autoheal/run"
    }
  }
}
```

---

### Application Metrics

**Endpoint**: `GET /metrics`

**Description**: Get application-level metrics (uptime, operation counts, success rate).

**Response**:
```json
{
  "uptime_seconds": 3661.2,
  "total_operations": 245,
  "successful": 241,
  "failed": 4,
  "success_rate_percent": 98.37
}
```

---

### Agent Status

**Endpoint**: `GET /agents/status`

**Description**: Get status of scheduler and all agents, including metrics and next execution times.

**Response**:
```json
{
  "scheduler": {
    "running": true,
    "jobs": [
      {
        "id": "health_agent",
        "name": "Indexer Health Check (every 30 minutes)",
        "next_run": "2025-01-14T11:00:00Z"
      },
      {
        "id": "autoheal_agent",
        "name": "Indexer Autoheal (every 2 hours)",
        "next_run": "2025-01-14T12:00:00Z"
      }
    ]
  },
  "agents": {
    "health_agent": {
      "name": "IndexerHealthAgent",
      "state": "idle",
      "enabled": true,
      "priority": "HIGH",
      "metrics": {
        "total_runs": 47,
        "successful_runs": 46,
        "failed_runs": 1,
        "success_rate": "97.9%",
        "average_duration": "2.34s",
        "last_run": "2025-01-14T10:30:02Z"
      }
    }
  }
}
```

---

### Startup Status

**Endpoint**: `GET /startup-status`

**Description**: Check if application has completed startup and all agents are initialized.

**Response**:
```json
{
  "complete": true,
  "agents_initialized": true,
  "agents_run": {
    "health_check": true,
    "autoheal": true,
    "discovery": false
  },
  "startup_time": "2025-01-14T10:00:00Z",
  "startup_duration_seconds": 2.34
}
```

---

## Indexer Management

### List All Indexers

**Endpoint**: `GET /indexers`

**Description**: Get list of all indexers from all services (Radarr, Sonarr, Prowlarr).

**Response**:
```json
{
  "radarr": {
    "total": 3,
    "enabled": 2,
    "disabled": 1,
    "indexers": [
      {
        "id": 1,
        "name": "BluRay",
        "enable": true
      },
      {
        "id": 2,
        "name": "NZB.su",
        "enable": false
      }
    ]
  },
  "sonarr": {
    "total": 2,
    "enabled": 2,
    "disabled": 0,
    "indexers": [
      {
        "id": 1,
        "name": "TVReleases",
        "enable": true
      }
    ]
  }
}
```

---

### List Indexers by Service

**Endpoint**: `GET /indexers/{service}`

**Parameters**:
- `service` (string, required): Service name - `radarr`, `sonarr`, or `prowlarr`

**Example**: `GET /indexers/radarr`

**Response**:
```json
{
  "service": "radarr",
  "count": 3,
  "indexers": [
    {
      "id": 1,
      "name": "BluRay",
      "enable": true,
      "protocol": "torrent"
    }
  ]
}
```

**Status Codes**:
- 200: Success
- 400: Invalid service name
- 500: Service error

---

### Test Indexer

**Endpoint**: `POST /indexers/{service}/{indexer_id}/test`

**Parameters**:
- `service` (string, required): `radarr` or `sonarr`
- `indexer_id` (integer, required): Indexer ID

**Example**: `POST /indexers/radarr/1/test`

**Response** (Success):
```json
{
  "success": true,
  "service": "radarr",
  "indexer_id": 1
}
```

**Response** (Failure):
```json
{
  "success": false,
  "service": "radarr",
  "indexer_id": 1,
  "error": "Connection timeout after 30 seconds"
}
```

---

### Disable Indexer

**Endpoint**: `POST /indexers/{service}/{indexer_id}/disable`

**Parameters**:
- `service` (string, required): `radarr` or `sonarr`
- `indexer_id` (integer, required): Indexer ID

**Example**: `POST /indexers/radarr/1/disable`

**Response**:
```json
{
  "success": true,
  "service": "radarr",
  "indexer_id": 1,
  "action": "disabled"
}
```

---

### Enable Indexer

**Endpoint**: `POST /indexers/{service}/{indexer_id}/enable`

**Parameters**:
- `service` (string, required): `radarr` or `sonarr`
- `indexer_id` (integer, required): Indexer ID

**Example**: `POST /indexers/radarr/1/enable`

**Response**:
```json
{
  "success": true,
  "service": "radarr",
  "indexer_id": 1,
  "action": "enabled"
}
```

---

### Indexer Statistics

**Endpoint**: `GET /indexers/stats`

**Description**: Get aggregated statistics about indexer status across all services.

**Response**:
```json
{
  "timestamp": "2025-01-14T10:35:00Z",
  "total": 5,
  "by_service": {
    "radarr": {
      "total": 3,
      "enabled": 2,
      "disabled": 1,
      "indexers": [...]
    },
    "sonarr": {
      "total": 2,
      "enabled": 2,
      "disabled": 0,
      "indexers": [...]
    }
  }
}
```

---

## Monitoring & Analytics

### Health History

**Endpoint**: `GET /health-history`

**Query Parameters**:
- `hours` (integer, optional): Number of hours to look back (default: 24)
- `limit` (integer, optional): Max records to return (default: 1000)

**Example**: `GET /health-history?hours=48&limit=100`

**Response**:
```json
{
  "hours": 48,
  "records_returned": 95,
  "query_time": "2025-01-14T10:35:00Z",
  "history": {
    "radarr": [
      {
        "id": 1,
        "indexer_id": 1,
        "name": "BluRay",
        "success": true,
        "error": null,
        "timestamp": "2025-01-14T10:30:00Z"
      }
    ],
    "sonarr": [...]
  }
}
```

---

### Detailed Statistics

**Endpoint**: `GET /stats/detailed`

**Query Parameters**:
- `days` (integer, optional): Days of data to analyze (default: 7)

**Response**:
```json
{
  "timestamp": "2025-01-14T10:35:00Z",
  "period_days": 7,
  "services": {
    "radarr": {
      "total_checks": 336,
      "total_indexers": 3,
      "enabled": 2,
      "health_stats": {
        "indexer_1": {
          "name": "BluRay",
          "total_checks": 112,
          "successes": 110,
          "failures": 2,
          "success_rate": 98.2,
          "last_failure": "2025-01-12T14:30:00Z"
        }
      }
    }
  }
}
```

---

### Recent Events

**Endpoint**: `GET /events`

**Query Parameters**:
- `limit` (integer, optional): Max events to return (default: 100)

**Example**: `GET /events?limit=50`

**Response**:
```json
{
  "timestamp": "2025-01-14T10:35:00Z",
  "events_count": 3,
  "events": [
    {
      "timestamp": "2025-01-14T10:30:02Z",
      "event_type": "agent_completed",
      "agent_name": "IndexerHealthAgent",
      "message": "Health check cycle completed successfully",
      "metadata": {
        "radarr_ok": true,
        "sonarr_ok": true
      }
    },
    {
      "timestamp": "2025-01-14T10:15:30Z",
      "event_type": "indexer_disabled",
      "agent_name": "IndexerAutoHealAgent",
      "message": "Disabled failing indexer",
      "metadata": {
        "service": "radarr",
        "indexer_id": 2,
        "indexer_name": "NZB.su"
      }
    }
  ]
}
```

---

## Agent Control

### Run Health Check

**Endpoint**: `POST /agents/health/run`

**Description**: Manually trigger the health check agent immediately.

**Response**:
```json
{
  "success": true,
  "agent": "health_agent",
  "message": "Health check cycle completed successfully"
}
```

---

### Run Autoheal

**Endpoint**: `POST /agents/autoheal/run`

**Description**: Manually trigger the autoheal agent immediately.

**Response**:
```json
{
  "success": true,
  "agent": "autoheal_agent",
  "message": "Autoheal cycle completed with 0 actions"
}
```

---

### Run Discovery

**Endpoint**: `POST /agents/discovery/run`

**Description**: Manually trigger the discovery agent (if enabled).

**Response**:
```json
{
  "success": true,
  "agent": "discovery_agent",
  "message": "Discovery run completed"
}
```

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error description here"
}
```

### Common Status Codes

- `200`: Success
- `400`: Bad request (invalid parameter)
- `404`: Not found (indexer, service, or agent)
- `500`: Server error (service unavailable, etc.)
- `503`: Service temporarily unavailable

### Example Error Response

```bash
$ curl -X POST http://localhost:8000/indexers/invalid-service/1/test
```

```json
{
  "detail": "Unknown service: invalid-service"
}
```

---

## Rate Limiting

API currently has no rate limiting. For production deployments behind a reverse proxy (nginx, etc.), add rate limiting at the proxy level.

---

## WebSocket / Real-time Events

Not currently implemented. For now, poll the `/events` endpoint to get recent system events.

---

## Pagination

Large result sets are returned in full. For very large health histories, use the `limit` parameter on `/health-history` endpoint.

---

## Timestamps

All timestamps are ISO 8601 format in UTC (Z suffix).

Example: `2025-01-14T10:35:00Z`

---

## Interactive API Documentation

After starting the application, visit **`http://localhost:8000/docs`** for interactive Swagger UI documentation where you can test all endpoints directly in your browser.
