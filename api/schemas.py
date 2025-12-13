"""Pydantic schemas for API request/response validation.

Defines request and response models for all API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Request/Response Models

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status")
    service: str = Field(description="Service name")


class ServiceInfoResponse(BaseModel):
    """Service information response."""
    service: str
    version: str
    description: str
    endpoints: Dict[str, Dict[str, str]]


class IndexerInfo(BaseModel):
    """Details about a single indexer."""
    id: int
    name: str
    enable: bool = True


class ServiceIndexersResponse(BaseModel):
    """Response with list of indexers from a service."""
    service: str
    count: int
    indexers: List[Dict[str, Any]]


class TestIndexerResponse(BaseModel):
    """Response from testing an indexer."""
    success: bool
    service: str
    indexer_id: int
    error: Optional[str] = None


class IndexerActionResponse(BaseModel):
    """Response from enable/disable operations."""
    success: bool
    service: str
    indexer_id: int
    action: str


class IndexerStatsItem(BaseModel):
    """Statistics for a single service's indexers."""
    total: int
    enabled: int
    disabled: int
    indexers: List[Dict[str, Any]] = []


class IndexerStatsResponse(BaseModel):
    """Overall indexer statistics."""
    timestamp: Optional[str] = None
    total: int
    by_service: Dict[str, IndexerStatsItem]


class AgentRunResponse(BaseModel):
    """Response from running an agent."""
    success: bool
    agent: str
    message: str


class HealthRecord(BaseModel):
    """A single health check record."""
    id: int
    indexer_id: int
    name: str
    success: bool
    error: Optional[str] = None
    timestamp: str


class HealthHistoryResponse(BaseModel):
    """Health history response."""
    hours: int
    records_returned: int
    query_time: str
    history: Dict[str, List[HealthRecord]]


class ServiceHealthStats(BaseModel):
    """Health statistics for a service."""
    total_indexers: int
    enabled: int
    disabled: int
    health_checks: Dict[str, Any]
    recent_failures: List[Dict[str, Any]]


class DetailedStatsResponse(BaseModel):
    """Detailed statistics response."""
    generated_at: str
    total_records: int
    by_service: Dict[str, Any]


class JobInfo(BaseModel):
    """Information about a scheduled job."""
    id: str
    name: str
    next_run_time: Optional[str] = None
    trigger: str


class AgentStatusResponse(BaseModel):
    """Status of all agents and scheduler."""
    scheduler: Dict[str, Any]
    agents: Dict[str, str]


class AgentMetrics(BaseModel):
    """Agent execution metrics."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: str
    average_duration: str
    last_run: Optional[str] = None
    last_error: Optional[str] = None


class OrchestratorStatusResponse(BaseModel):
    """Orchestrator status response."""
    name: str
    running: bool
    agents: Dict[str, Dict[str, Any]]
    schedules: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]


class AgentHealthStatus(BaseModel):
    """Health status of an agent."""
    agent_name: str
    is_healthy: bool
    last_run: Optional[str] = None
    last_error: Optional[str] = None
    consecutive_failures: int
    uptime_percentage: str


class MonitorStatusResponse(BaseModel):
    """Monitor status response."""
    total_agents: int
    healthy_agents: int
    unhealthy_agents: int
    health_percentage: float
    total_events_logged: int
    recent_events: List[Dict[str, Any]]
    agent_health: Dict[str, Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    status_code: int
    timestamp: Optional[str] = None
