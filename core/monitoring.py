"""Monitoring and observability utilities."""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from loguru import logger


@dataclass
class HealthMetrics:
    """Health metrics snapshot."""
    timestamp: str
    uptime_seconds: float
    total_indexers: int
    healthy_indexers: int
    unhealthy_indexers: int
    success_rate: float
    recent_errors: int


class MetricsCollector:
    """Collects and manages application metrics."""
    
    def __init__(self) -> None:
        self.start_time = datetime.utcnow()
        self.error_count = 0
        self.success_count = 0
    
    def record_error(self) -> None:
        """Record an error occurrence."""
        self.error_count += 1
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self.success_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        total = self.error_count + self.success_count
        success_rate = (
            (self.success_count / total * 100) if total > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "total_operations": total,
            "successful": self.success_count,
            "failed": self.error_count,
            "success_rate_percent": round(success_rate, 2),
        }


class EventLog:
    """Structured event logging for audit trail."""
    
    def __init__(self, log_dir: Optional[Path] = None) -> None:
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.event_file = self.log_dir / "events.jsonl"
    
    def log_event(
        self,
        event_type: str,
        service: str,
        details: Dict[str, Any],
        severity: str = "INFO",
    ) -> None:
        """Log a structured event.
        
        Args:
            event_type: Type of event (e.g., "indexer_disabled", "health_check_failed")
            service: Service name (radarr, sonarr, prowlarr)
            details: Event details as dictionary
            severity: Event severity (INFO, WARNING, ERROR)
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "service": service,
            "severity": severity,
            "details": details,
        }
        
        try:
            with open(self.event_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write event log: {e}")
    
    def get_recent_events(self, limit: int = 100) -> list:
        """Get recent events from log file.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        events = []
        
        if not self.event_file.exists():
            return events
        
        try:
            with open(self.event_file, "r") as f:
                lines = f.readlines()
                # Get last N lines
                for line in lines[-limit:]:
                    try:
                        event = json.loads(line.strip())
                        events.append(event)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Failed to read event log: {e}")
        
        return events


class StartupStatus:
    """Tracks application startup status and completion."""
    
    def __init__(self) -> None:
        self.startup_complete = False
        self.startup_time: Optional[datetime] = None
        self.startup_errors: list = []
        self.agents_run: Dict[str, bool] = {
            "health_check": False,
            "autoheal": False,
            "discovery": False,
        }
    
    def mark_startup_start(self) -> None:
        """Mark startup as starting."""
        self.startup_time = datetime.utcnow()
        self.startup_complete = False
    
    def mark_agent_run(self, agent_name: str) -> None:
        """Mark an agent as having run during startup."""
        if agent_name in self.agents_run:
            self.agents_run[agent_name] = True
    
    def record_startup_error(self, agent_name: str, error: str) -> None:
        """Record an error during startup."""
        self.startup_errors.append({
            "agent": agent_name,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def mark_startup_complete(self) -> None:
        """Mark startup as complete."""
        self.startup_complete = True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current startup status."""
        status = {
            "complete": self.startup_complete,
            "agents_initialized": all(self.agents_run.values()),
            "agents_run": self.agents_run,
        }
        
        if self.startup_time:
            status["startup_time"] = self.startup_time.isoformat()
            status["startup_duration_seconds"] = (
                datetime.utcnow() - self.startup_time
            ).total_seconds()
        
        if self.startup_errors:
            status["errors"] = self.startup_errors
        
        return status


# Global instances
metrics_collector = MetricsCollector()
event_log = EventLog()
startup_status = StartupStatus()
