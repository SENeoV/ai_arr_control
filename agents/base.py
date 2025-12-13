"""Base classes for AI agent framework.

This module provides abstract base classes and interfaces for building
autonomous agents with standardized execution, monitoring, and state
management capabilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List
from loguru import logger


class AgentState(str, Enum):
    """Enumeration of possible agent execution states."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentPriority(int, Enum):
    """Execution priority levels for agents."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class AgentMetrics:
    """Metrics tracked for each agent execution."""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_duration_seconds: float = 0.0
    last_run_start: Optional[datetime] = None
    last_run_end: Optional[datetime] = None
    last_error: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100

    @property
    def average_duration(self) -> float:
        """Calculate average execution duration."""
        if self.total_runs == 0:
            return 0.0
        return self.total_duration_seconds / self.total_runs


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    message: str
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} {self.message}"


class Agent(ABC):
    """Abstract base class for autonomous agents.
    
    All agents must implement the run() method and optionally override
    validate_config() and cleanup() for configuration validation and
    resource cleanup respectively.
    """

    def __init__(
        self,
        name: str,
        priority: AgentPriority = AgentPriority.NORMAL,
        enabled: bool = True,
    ) -> None:
        """Initialize agent with name and configuration.

        Args:
            name: Unique identifier for the agent
            priority: Execution priority level
            enabled: Whether the agent should run
        """
        self.name = name
        self.priority = priority
        self.enabled = enabled
        self.state = AgentState.IDLE
        self.metrics = AgentMetrics()
        self._dependencies: List[str] = []
        logger.info(f"Initialized agent: {name} (priority={priority.name})")

    def register_dependency(self, agent_name: str) -> None:
        """Register a dependency on another agent.

        Args:
            agent_name: Name of the agent this agent depends on
        """
        if agent_name not in self._dependencies:
            self._dependencies.append(agent_name)

    @property
    def dependencies(self) -> List[str]:
        """Get list of agent dependencies."""
        return self._dependencies.copy()

    @abstractmethod
    async def run(self) -> AgentResult:
        """Execute the agent's primary task.

        This method must be implemented by subclasses. It should:
        - Perform the agent's core logic
        - Return an AgentResult with success status and details
        - Not raise exceptions (catch and log them)
        - Update internal metrics

        Returns:
            AgentResult containing execution outcome and metrics
        """
        pass

    async def validate_config(self) -> bool:
        """Validate agent configuration at startup.

        Override this method to perform configuration validation.
        Return False if validation fails.

        Returns:
            True if configuration is valid, False otherwise
        """
        return True

    async def cleanup(self) -> None:
        """Cleanup resources when agent is stopped.

        Override this method to clean up any resources held by the agent
        (connections, file handles, etc.).
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics.

        Returns:
            Dictionary containing state, metrics, and status information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "enabled": self.enabled,
            "priority": self.priority.name,
            "metrics": {
                "total_runs": self.metrics.total_runs,
                "successful_runs": self.metrics.successful_runs,
                "failed_runs": self.metrics.failed_runs,
                "success_rate": f"{self.metrics.success_rate:.1f}%",
                "average_duration": f"{self.metrics.average_duration:.2f}s",
                "last_run": self.metrics.last_run_end.isoformat()
                if self.metrics.last_run_end
                else None,
                "last_error": self.metrics.last_error,
            },
            "dependencies": self._dependencies,
        }


class AgentChain:
    """Orchestrates execution of multiple agents with dependency management."""

    def __init__(self) -> None:
        """Initialize agent chain."""
        self.agents: Dict[str, Agent] = {}
        self.execution_order: List[str] = []

    def register(self, agent: Agent) -> None:
        """Register an agent in the chain.

        Args:
            agent: Agent instance to register
            
        Raises:
            ValueError: If an agent with the same name already exists
        """
        if agent.name in self.agents:
            raise ValueError(f"Agent '{agent.name}' already registered")

        self.agents[agent.name] = agent
        logger.debug(f"Registered agent: {agent.name}")

    def _resolve_execution_order(self) -> List[str]:
        """Resolve execution order based on dependencies.

        Uses topological sort to ensure dependencies run before dependents.

        Returns:
            Ordered list of agent names for execution

        Raises:
            ValueError: If circular dependencies are detected
        """
        in_degree = {name: 0 for name in self.agents}
        graph: Dict[str, List[str]] = {name: [] for name in self.agents}

        # Build dependency graph
        for name, agent in self.agents.items():
            for dep in agent.dependencies:
                if dep in self.agents:
                    graph[dep].append(name)
                    in_degree[name] += 1
                else:
                    logger.warning(f"Agent '{name}' depends on unknown agent '{dep}'")

        # Topological sort using Kahn's algorithm
        queue = [name for name in self.agents if in_degree[name] == 0]
        result = []

        while queue:
            # Sort by priority (lower number = higher priority)
            queue.sort(key=lambda n: self.agents[n].priority.value)
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.agents):
            raise ValueError("Circular dependency detected in agent chain")

        return result

    async def execute(self, agent_name: Optional[str] = None) -> List[AgentResult]:
        """Execute agents in dependency order.

        Args:
            agent_name: If specified, execute only this agent and its dependents

        Returns:
            List of AgentResult objects in execution order
        """
        self.execution_order = self._resolve_execution_order()
        results = []

        # Filter agents if specific agent requested
        agents_to_run = self.execution_order
        if agent_name:
            if agent_name not in self.agents:
                logger.error(f"Agent '{agent_name}' not found")
                return []
            agents_to_run = [agent_name]

        for agent_name in agents_to_run:
            agent = self.agents[agent_name]

            if not agent.enabled:
                logger.debug(f"Skipping disabled agent: {agent_name}")
                continue

            logger.info(f"Executing agent: {agent_name}")
            agent.state = AgentState.RUNNING

            try:
                result = await agent.run()
                results.append(result)

                # Update metrics
                agent.metrics.total_runs += 1
                agent.metrics.last_run_start = result.timestamp
                agent.metrics.last_run_end = datetime.utcnow()

                if result.success:
                    agent.metrics.successful_runs += 1
                    agent.state = AgentState.COMPLETED
                    logger.info(f"Agent {agent_name} completed: {result.message}")
                else:
                    agent.metrics.failed_runs += 1
                    agent.metrics.last_error = result.error
                    agent.state = AgentState.FAILED
                    logger.warning(f"Agent {agent_name} failed: {result.error}")

            except Exception as e:
                logger.exception(f"Unexpected error in agent {agent_name}: {e}")
                agent.state = AgentState.FAILED
                agent.metrics.failed_runs += 1
                agent.metrics.last_error = str(e)

        return results
