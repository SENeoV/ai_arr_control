"""Agent orchestrator for coordinating autonomous agents.

The orchestrator manages agent lifecycle, scheduling, monitoring, and
coordination across multiple autonomous agents working toward common goals.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
import asyncio
from loguru import logger

from agents.base import Agent, AgentResult, AgentState

# Get current UTC time in a timezone-aware manner
def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class AgentSchedule:
    """Schedule configuration for periodic agent execution."""
    agent_name: str
    interval_seconds: int
    enabled: bool = True
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    max_concurrent_runs: int = 1

    def should_execute(self) -> bool:
        """Check if agent should execute based on schedule."""
        if not self.enabled:
            return False

        if self.next_execution is None:
            return True

        return utc_now() >= self.next_execution

    def update_next_execution(self) -> None:
        """Update next execution time after a run."""
        self.last_executed = utc_now()
        self.next_execution = self.last_executed + timedelta(
            seconds=self.interval_seconds
        )


@dataclass
class OrchestratorMetrics:
    """Metrics for orchestrator performance."""
    total_cycles: int = 0
    successful_cycles: int = 0
    failed_cycles: int = 0
    total_agent_runs: int = 0
    total_agent_successes: int = 0
    total_agent_failures: int = 0
    cycle_duration_seconds: float = 0.0
    started_at: datetime = field(default_factory=utc_now)

    @property
    def uptime_seconds(self) -> float:
        """Calculate orchestrator uptime."""
        return (utc_now() - self.started_at).total_seconds()

    @property
    def cycle_success_rate(self) -> float:
        """Calculate success rate of execution cycles."""
        if self.total_cycles == 0:
            return 0.0
        return (self.successful_cycles / self.total_cycles) * 100

    @property
    def agent_success_rate(self) -> float:
        """Calculate success rate of agent executions."""
        if self.total_agent_runs == 0:
            return 0.0
        return (self.total_agent_successes / self.total_agent_runs) * 100


class AgentOrchestrator:
    """Orchestrates execution, scheduling, and monitoring of agents.

    The orchestrator provides:
    - Agent registration and lifecycle management
    - Periodic scheduling with configurable intervals
    - Dependency resolution and execution ordering
    - Comprehensive metrics and monitoring
    - Event logging and observability
    """

    def __init__(self, name: str = "DefaultOrchestrator") -> None:
        """Initialize orchestrator.

        Args:
            name: Name identifier for this orchestrator instance
        """
        self.name = name
        self.agents: Dict[str, Agent] = {}
        self.schedules: Dict[str, AgentSchedule] = {}
        self.metrics = OrchestratorMetrics()
        self._running = False
        self._execution_lock = asyncio.Lock()
        self._active_runs: Dict[str, int] = {}
        logger.info(f"Initialized orchestrator: {name}")

    def register_agent(
        self, agent: Agent, interval_seconds: Optional[int] = None
    ) -> None:
        """Register an agent with the orchestrator.

        Args:
            agent: Agent instance to register
            interval_seconds: If provided, schedule periodic execution

        Raises:
            ValueError: If an agent with the same name already exists
        """
        if agent.name in self.agents:
            raise ValueError(f"Agent '{agent.name}' already registered")

        self.agents[agent.name] = agent
        self._active_runs[agent.name] = 0

        if interval_seconds is not None:
            schedule = AgentSchedule(
                agent_name=agent.name,
                interval_seconds=interval_seconds,
                next_execution=utc_now(),
            )
            self.schedules[agent.name] = schedule
            logger.info(
                f"Scheduled agent '{agent.name}' with interval {interval_seconds}s"
            )
        else:
            logger.debug(f"Registered agent '{agent.name}' (on-demand only)")

    def unregister_agent(self, agent_name: str) -> bool:
        """Unregister an agent from the orchestrator.

        Args:
            agent_name: Name of the agent to unregister

        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_name not in self.agents:
            return False

        del self.agents[agent_name]
        self.schedules.pop(agent_name, None)
        self._active_runs.pop(agent_name, None)
        logger.info(f"Unregistered agent: {agent_name}")
        return True

    def enable_agent(self, agent_name: str) -> bool:
        """Enable a registered agent.

        Args:
            agent_name: Name of the agent to enable

        Returns:
            True if agent was enabled, False if not found
        """
        if agent_name not in self.agents:
            return False

        self.agents[agent_name].enabled = True
        if agent_name in self.schedules:
            self.schedules[agent_name].enabled = True
        logger.info(f"Enabled agent: {agent_name}")
        return True

    def disable_agent(self, agent_name: str) -> bool:
        """Disable a registered agent.

        Args:
            agent_name: Name of the agent to disable

        Returns:
            True if agent was disabled, False if not found
        """
        if agent_name not in self.agents:
            return False

        self.agents[agent_name].enabled = False
        if agent_name in self.schedules:
            self.schedules[agent_name].enabled = False
        logger.info(f"Disabled agent: {agent_name}")
        return True

    async def execute_agent(self, agent_name: str) -> Optional[AgentResult]:
        """Execute a specific agent on-demand.

        Args:
            agent_name: Name of the agent to execute

        Returns:
            AgentResult if successful, None if agent not found or already running
        """
        if agent_name not in self.agents:
            logger.error(f"Agent '{agent_name}' not found")
            return None

        agent = self.agents[agent_name]
        schedule = self.schedules.get(agent_name)

        # Check concurrency limit
        if schedule and self._active_runs[agent_name] >= schedule.max_concurrent_runs:
            logger.warning(
                f"Agent '{agent_name}' already at max concurrent runs ({schedule.max_concurrent_runs})"
            )
            return None

        async with self._execution_lock:
            self._active_runs[agent_name] += 1

        try:
            logger.debug(f"Starting execution of agent: {agent_name}")
            agent.state = AgentState.RUNNING
            result = await agent.run()

            # Update metrics
            self.metrics.total_agent_runs += 1
            if result.success:
                self.metrics.total_agent_successes += 1
            else:
                self.metrics.total_agent_failures += 1

            return result

        except Exception as e:
            logger.exception(f"Error executing agent {agent_name}: {e}")
            self.metrics.total_agent_failures += 1
            return None

        finally:
            async with self._execution_lock:
                self._active_runs[agent_name] = max(0, self._active_runs[agent_name] - 1)

            # Update schedule
            if schedule:
                schedule.update_next_execution()

    async def execute_scheduled_agents(self) -> List[AgentResult]:
        """Execute all agents whose schedules are due.

        Returns:
            List of AgentResult objects from executed agents
        """
        results = []

        for agent_name, schedule in self.schedules.items():
            if schedule.should_execute():
                logger.debug(f"Schedule check: executing {agent_name}")
                result = await self.execute_agent(agent_name)
                if result:
                    results.append(result)

        return results

    async def start(self, check_interval: float = 60.0) -> None:
        """Start the orchestrator's main event loop.

        Continuously monitors schedules and executes agents as needed.

        Args:
            check_interval: Seconds between schedule checks (default: 60)
        """
        if self._running:
            logger.warning("Orchestrator already running")
            return

        self._running = True
        logger.info(f"Starting orchestrator: {self.name}")

        try:
            while self._running:
                try:
                    results = await self.execute_scheduled_agents()

                    if results:
                        self.metrics.total_cycles += 1
                        success_count = sum(
                            1 for r in results if r.success
                        )
                        if success_count == len(results):
                            self.metrics.successful_cycles += 1
                        else:
                            self.metrics.failed_cycles += 1

                    await asyncio.sleep(check_interval)

                except Exception as e:
                    logger.exception(f"Error in orchestrator cycle: {e}")
                    self.metrics.failed_cycles += 1
                    self.metrics.total_cycles += 1
                    await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            logger.info("Orchestrator shutdown requested")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the orchestrator and cleanup all agents."""
        logger.info(f"Stopping orchestrator: {self.name}")
        self._running = False

        # Cleanup all agents
        for agent in self.agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent.name}: {e}")

        logger.info(f"Orchestrator stopped: {self.name}")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status.

        Returns:
            Dictionary containing status, metrics, and agent information
        """
        return {
            "name": self.name,
            "running": self._running,
            "agents": {
                name: agent.get_status() for name, agent in self.agents.items()
            },
            "schedules": {
                name: {
                    "interval_seconds": schedule.interval_seconds,
                    "enabled": schedule.enabled,
                    "last_executed": schedule.last_executed.isoformat()
                    if schedule.last_executed
                    else None,
                    "next_execution": schedule.next_execution.isoformat()
                    if schedule.next_execution
                    else None,
                    "active_runs": self._active_runs.get(name, 0),
                }
                for name, schedule in self.schedules.items()
            },
            "metrics": {
                "total_cycles": self.metrics.total_cycles,
                "successful_cycles": self.metrics.successful_cycles,
                "failed_cycles": self.metrics.failed_cycles,
                "cycle_success_rate": f"{self.metrics.cycle_success_rate:.1f}%",
                "total_agent_runs": self.metrics.total_agent_runs,
                "total_agent_successes": self.metrics.total_agent_successes,
                "total_agent_failures": self.metrics.total_agent_failures,
                "agent_success_rate": f"{self.metrics.agent_success_rate:.1f}%",
                "uptime_seconds": self.metrics.uptime_seconds,
            },
        }
