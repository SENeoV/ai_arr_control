"""Agent monitoring and state management.

Provides comprehensive monitoring, state tracking, and event logging
for agent operations with detailed metrics and observability.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from loguru import logger


class EventType(str, Enum):
    """Types of events that can be logged."""
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_DISABLED = "agent_disabled"
    AGENT_ENABLED = "agent_enabled"
    ORCHESTRATOR_STARTED = "orchestrator_started"
    ORCHESTRATOR_STOPPED = "orchestrator_stopped"
    AGENT_DEPENDENCY_FAILED = "agent_dependency_failed"
    CONFIG_VALIDATED = "config_validated"
    ERROR_ENCOUNTERED = "error_encountered"


@dataclass
class Event:
    """Represents a monitored event."""
    event_type: EventType
    agent_name: Optional[str]
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.event_type.value} - {self.message}"


@dataclass
class AgentHealthStatus:
    """Health status of an agent."""
    agent_name: str
    is_healthy: bool = True
    last_run: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "is_healthy": self.is_healthy,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "uptime_percentage": f"{self.uptime_percentage:.1f}%",
        }


class AgentMonitor:
    """Comprehensive monitoring for agent execution.
    
    Tracks:
    - Event history
    - Agent health status
    - Performance metrics
    - Error conditions and thresholds
    """

    def __init__(self, max_event_history: int = 1000) -> None:
        """Initialize monitor.

        Args:
            max_event_history: Maximum number of events to keep in memory
        """
        self.max_event_history = max_event_history
        self.events: List[Event] = []
        self.agent_health: Dict[str, AgentHealthStatus] = {}
        self.error_threshold = 3  # Max consecutive failures before alerting
        logger.info(f"Initialized AgentMonitor (max_events={max_event_history})")

    def record_event(
        self,
        event_type: EventType,
        agent_name: Optional[str] = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a monitored event.

        Args:
            event_type: Type of event
            agent_name: Name of agent involved (if applicable)
            message: Event message
            metadata: Additional metadata to attach
        """
        event = Event(
            event_type=event_type,
            agent_name=agent_name,
            message=message,
            metadata=metadata or {},
        )
        self.events.append(event)

        # Maintain size limit
        if len(self.events) > self.max_event_history:
            self.events = self.events[-self.max_event_history :]

        logger.debug(f"Event recorded: {event}")

    def update_agent_health(
        self,
        agent_name: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Update agent health status based on execution result.

        Args:
            agent_name: Name of the agent
            success: Whether the execution was successful
            error: Error message if failed
        """
        if agent_name not in self.agent_health:
            self.agent_health[agent_name] = AgentHealthStatus(agent_name=agent_name)

        status = self.agent_health[agent_name]
        status.last_run = datetime.utcnow()

        if success:
            status.consecutive_failures = 0
            status.is_healthy = True
            status.last_error = None
        else:
            status.consecutive_failures += 1
            status.last_error = error
            
            if status.consecutive_failures >= self.error_threshold:
                status.is_healthy = False
                logger.warning(
                    f"Agent '{agent_name}' marked unhealthy after "
                    f"{status.consecutive_failures} consecutive failures"
                )
                self.record_event(
                    EventType.AGENT_FAILED,
                    agent_name,
                    f"Agent marked unhealthy: {status.consecutive_failures} failures",
                    {"consecutive_failures": status.consecutive_failures},
                )

    def get_agent_health(self, agent_name: str) -> Optional[AgentHealthStatus]:
        """Get health status for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentHealthStatus or None if not found
        """
        return self.agent_health.get(agent_name)

    def get_all_health(self) -> Dict[str, AgentHealthStatus]:
        """Get health status for all agents.

        Returns:
            Dictionary of agent names to health statuses
        """
        return self.agent_health.copy()

    def get_unhealthy_agents(self) -> List[str]:
        """Get list of agents currently marked unhealthy.

        Returns:
            List of unhealthy agent names
        """
        return [
            name for name, status in self.agent_health.items() if not status.is_healthy
        ]

    def get_events(
        self,
        agent_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Query events with optional filtering.

        Args:
            agent_name: Filter to specific agent (optional)
            event_type: Filter to specific event type (optional)
            limit: Maximum events to return

        Returns:
            List of matching events (most recent first)
        """
        results = []

        for event in reversed(self.events):
            if agent_name and event.agent_name != agent_name:
                continue
            if event_type and event.event_type != event_type:
                continue
            results.append(event)
            if len(results) >= limit:
                break

        return results

    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary.

        Returns:
            Dictionary with overall health and metrics
        """
        total_agents = len(self.agent_health)
        unhealthy = len(self.get_unhealthy_agents())
        healthy = total_agents - unhealthy

        recent_events = self.get_events(limit=10)

        return {
            "total_agents": total_agents,
            "healthy_agents": healthy,
            "unhealthy_agents": unhealthy,
            "health_percentage": (
                (healthy / total_agents * 100) if total_agents > 0 else 0
            ),
            "total_events_logged": len(self.events),
            "recent_events": [
                {
                    "type": e.event_type.value,
                    "agent": e.agent_name,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in recent_events
            ],
            "agent_health": {
                name: status.to_dict() for name, status in self.agent_health.items()
            },
        }
