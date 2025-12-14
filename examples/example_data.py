"""Example configurations and test data for AI Arr Control."""

# Example Radarr/Sonarr indexer responses (typical API structure)
EXAMPLE_RADARR_INDEXERS = [
    {
        "id": 1,
        "name": "BluRay",
        "protocol": "torrent",
        "settings": {},
        "tags": [1, 2],
        "enable": True,
        "redirect": False,
    },
    {
        "id": 2,
        "name": "NZB.su",
        "protocol": "usenet",
        "settings": {},
        "tags": [],
        "enable": False,  # Disabled indexer
        "redirect": False,
    },
    {
        "id": 3,
        "name": "Xtreme",
        "protocol": "torrent",
        "settings": {},
        "tags": [1],
        "enable": True,
        "redirect": False,
    },
]

EXAMPLE_SONARR_INDEXERS = [
    {
        "id": 1,
        "name": "TVReleases",
        "protocol": "torrent",
        "settings": {},
        "tags": [1],
        "enable": True,
        "redirect": False,
    },
    {
        "id": 2,
        "name": "Usenet.Farm",
        "protocol": "usenet",
        "settings": {},
        "tags": [1, 2],
        "enable": True,
        "redirect": False,
    },
]

EXAMPLE_PROWLARR_INDEXERS = [
    {
        "id": 1,
        "name": "BluRay",
        "protocol": "torrent",
        "categories": [2010],
        "enable": True,
        "fields": [],
    },
    {
        "id": 2,
        "name": "NZB.su",
        "protocol": "usenet",
        "categories": [5000],
        "enable": True,
        "fields": [],
    },
]

# Example health check history
EXAMPLE_HEALTH_HISTORY = {
    "radarr": [
        {
            "id": 1,
            "indexer_id": 1,
            "name": "BluRay",
            "success": True,
            "error": None,
            "timestamp": "2025-01-14T10:30:00Z",
        },
        {
            "id": 2,
            "indexer_id": 2,
            "name": "NZB.su",
            "success": False,
            "error": "Connection timeout",
            "timestamp": "2025-01-14T10:30:15Z",
        },
    ],
    "sonarr": [
        {
            "id": 3,
            "indexer_id": 1,
            "name": "TVReleases",
            "success": True,
            "error": None,
            "timestamp": "2025-01-14T10:30:00Z",
        },
    ],
}

# Example application stats
EXAMPLE_STATS = {
    "timestamp": "2025-01-14T10:35:00Z",
    "total": 5,
    "by_service": {
        "radarr": {
            "total": 3,
            "enabled": 2,
            "disabled": 1,
            "indexers": [
                {"id": 1, "name": "BluRay", "enable": True},
                {"id": 2, "name": "NZB.su", "enable": False},
                {"id": 3, "name": "Xtreme", "enable": True},
            ],
        },
        "sonarr": {
            "total": 2,
            "enabled": 2,
            "disabled": 0,
            "indexers": [
                {"id": 1, "name": "TVReleases", "enable": True},
                {"id": 2, "name": "Usenet.Farm", "enable": True},
            ],
        },
    },
}

# Example metrics response
EXAMPLE_METRICS = {
    "uptime_seconds": 3661.2,
    "total_operations": 245,
    "successful": 241,
    "failed": 4,
    "success_rate_percent": 98.37,
}

# Example agent status
EXAMPLE_AGENT_STATUS = {
    "scheduler": {
        "running": True,
        "jobs": [
            {
                "id": "health_agent",
                "name": "Indexer Health Check (every 30 minutes)",
                "next_run": "2025-01-14T11:00:00Z",
            },
            {
                "id": "autoheal_agent",
                "name": "Indexer Autoheal (every 2 hours)",
                "next_run": "2025-01-14T12:00:00Z",
            },
        ],
    },
    "agents": {
        "health_agent": {
            "name": "IndexerHealthAgent",
            "state": "idle",
            "enabled": True,
            "priority": "HIGH",
            "metrics": {
                "total_runs": 47,
                "successful_runs": 46,
                "failed_runs": 1,
                "success_rate": "97.9%",
                "average_duration": "2.34s",
                "last_run": "2025-01-14T10:30:02Z",
                "last_error": None,
            },
            "dependencies": [],
        },
        "autoheal_agent": {
            "name": "IndexerAutoHealAgent",
            "state": "idle",
            "enabled": True,
            "priority": "HIGH",
            "metrics": {
                "total_runs": 23,
                "successful_runs": 23,
                "failed_runs": 0,
                "success_rate": "100.0%",
                "average_duration": "1.45s",
                "last_run": "2025-01-14T10:00:05Z",
                "last_error": None,
            },
            "dependencies": ["health_agent"],
        },
    },
}

# Example event log
EXAMPLE_EVENTS = {
    "timestamp": "2025-01-14T10:35:00Z",
    "events_count": 3,
    "events": [
        {
            "timestamp": "2025-01-14T10:30:02Z",
            "event_type": "agent_completed",
            "agent_name": "IndexerHealthAgent",
            "message": "Health check cycle completed successfully",
            "metadata": {"radarr_ok": True, "sonarr_ok": True},
        },
        {
            "timestamp": "2025-01-14T10:15:30Z",
            "event_type": "indexer_disabled",
            "agent_name": "IndexerAutoHealAgent",
            "message": "Disabled failing indexer",
            "metadata": {"service": "radarr", "indexer_id": 2, "indexer_name": "NZB.su"},
        },
        {
            "timestamp": "2025-01-14T10:00:05Z",
            "event_type": "agent_completed",
            "agent_name": "IndexerAutoHealAgent",
            "message": "Autoheal cycle completed",
            "metadata": {"actions_taken": 1},
        },
    ],
}

# Example startup status
EXAMPLE_STARTUP_STATUS = {
    "complete": True,
    "agents_initialized": True,
    "agents_run": {
        "health_check": True,
        "autoheal": True,
        "discovery": False,
    },
    "startup_time": "2025-01-14T10:00:00Z",
    "startup_duration_seconds": 2.34,
}
