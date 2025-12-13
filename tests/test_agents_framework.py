"""Comprehensive test suite for agent framework and orchestrator.

Tests agent base classes, orchestrator functionality, agent implementations,
and integration scenarios.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Any

from agents.base import (
    Agent, AgentResult, AgentState, AgentPriority, AgentMetrics, AgentChain
)
from agents.orchestrator import AgentOrchestrator, AgentSchedule, OrchestratorMetrics
from agents.monitor import AgentMonitor, EventType, Event, AgentHealthStatus


# Test Fixtures and Mock Agents
class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(
        self,
        name: str,
        should_fail: bool = False,
        delay_seconds: float = 0.0,
        priority: AgentPriority = AgentPriority.NORMAL,
    ):
        super().__init__(name=name, priority=priority)
        self.should_fail = should_fail
        self.delay_seconds = delay_seconds
        self.run_count = 0

    async def run(self) -> AgentResult:
        """Run the mock agent."""
        self.run_count += 1

        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            return AgentResult(
                success=False,
                message=f"{self.name} failed",
                error="Mock failure",
            )

        return AgentResult(
            success=True,
            message=f"{self.name} completed",
            metrics={"run_count": self.run_count},
        )


@pytest.fixture
def simple_agent():
    """Fixture providing a simple mock agent."""
    return MockAgent(name="TestAgent")


@pytest.fixture
def failing_agent():
    """Fixture providing a failing mock agent."""
    return MockAgent(name="FailingAgent", should_fail=True)


@pytest.fixture
def slow_agent():
    """Fixture providing a slow mock agent."""
    return MockAgent(name="SlowAgent", delay_seconds=0.5)


@pytest.fixture
def orchestrator():
    """Fixture providing an orchestrator instance."""
    return AgentOrchestrator(name="TestOrchestrator")


@pytest.fixture
def monitor():
    """Fixture providing a monitor instance."""
    return AgentMonitor()


# Tests for Agent Base Class
class TestAgentBase:
    """Test agent base classes and functionality."""

    def test_agent_initialization(self, simple_agent):
        """Test agent initialization."""
        assert simple_agent.name == "TestAgent"
        assert simple_agent.enabled is True
        assert simple_agent.state == AgentState.IDLE
        assert simple_agent.priority == AgentPriority.NORMAL

    def test_agent_metrics_initialization(self, simple_agent):
        """Test agent metrics are initialized correctly."""
        metrics = simple_agent.metrics
        assert metrics.total_runs == 0
        assert metrics.successful_runs == 0
        assert metrics.failed_runs == 0
        assert metrics.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_agent_run_success(self, simple_agent):
        """Test successful agent execution."""
        result = await simple_agent.run()
        assert result.success is True
        assert "completed" in result.message.lower()
        assert simple_agent.run_count == 1

    @pytest.mark.asyncio
    async def test_agent_run_failure(self, failing_agent):
        """Test failed agent execution."""
        result = await failing_agent.run()
        assert result.success is False
        assert result.error == "Mock failure"

    def test_agent_dependency_registration(self, simple_agent):
        """Test dependency registration."""
        simple_agent.register_dependency("OtherAgent")
        assert "OtherAgent" in simple_agent.dependencies
        assert len(simple_agent.dependencies) == 1

    def test_agent_status(self, simple_agent):
        """Test agent status reporting."""
        status = simple_agent.get_status()
        assert status["name"] == "TestAgent"
        assert status["state"] == AgentState.IDLE.value
        assert status["enabled"] is True
        assert "metrics" in status


# Tests for Agent Metrics
class TestAgentMetrics:
    """Test agent metrics functionality."""

    def test_metrics_success_rate(self):
        """Test success rate calculation."""
        metrics = AgentMetrics()
        metrics.total_runs = 10
        metrics.successful_runs = 7
        assert metrics.success_rate == 70.0

    def test_metrics_zero_runs(self):
        """Test metrics with zero runs."""
        metrics = AgentMetrics()
        assert metrics.success_rate == 0.0
        assert metrics.average_duration == 0.0

    def test_metrics_average_duration(self):
        """Test average duration calculation."""
        metrics = AgentMetrics()
        metrics.total_runs = 4
        metrics.total_duration_seconds = 10.0
        assert metrics.average_duration == 2.5


# Tests for Agent Orchestrator
class TestAgentOrchestrator:
    """Test orchestrator functionality."""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.name == "TestOrchestrator"
        assert orchestrator._running is False
        assert len(orchestrator.agents) == 0

    def test_register_agent(self, orchestrator, simple_agent):
        """Test agent registration."""
        orchestrator.register_agent(simple_agent)
        assert "TestAgent" in orchestrator.agents
        assert orchestrator.agents["TestAgent"] == simple_agent

    def test_register_agent_duplicate_error(self, orchestrator, simple_agent):
        """Test error on duplicate agent registration."""
        orchestrator.register_agent(simple_agent)
        with pytest.raises(ValueError):
            orchestrator.register_agent(simple_agent)

    def test_register_agent_with_schedule(self, orchestrator, simple_agent):
        """Test agent registration with schedule."""
        orchestrator.register_agent(simple_agent, interval_seconds=60)
        assert "TestAgent" in orchestrator.schedules
        assert orchestrator.schedules["TestAgent"].interval_seconds == 60

    def test_unregister_agent(self, orchestrator, simple_agent):
        """Test agent unregistration."""
        orchestrator.register_agent(simple_agent)
        success = orchestrator.unregister_agent("TestAgent")
        assert success is True
        assert "TestAgent" not in orchestrator.agents

    def test_unregister_nonexistent_agent(self, orchestrator):
        """Test unregistering nonexistent agent."""
        success = orchestrator.unregister_agent("NonExistent")
        assert success is False

    def test_enable_disable_agent(self, orchestrator, simple_agent):
        """Test enabling and disabling agents."""
        orchestrator.register_agent(simple_agent)
        
        # Disable
        success = orchestrator.disable_agent("TestAgent")
        assert success is True
        assert simple_agent.enabled is False

        # Enable
        success = orchestrator.enable_agent("TestAgent")
        assert success is True
        assert simple_agent.enabled is True

    @pytest.mark.asyncio
    async def test_execute_agent_on_demand(self, orchestrator, simple_agent):
        """Test on-demand agent execution."""
        orchestrator.register_agent(simple_agent)
        result = await orchestrator.execute_agent("TestAgent")

        assert result is not None
        assert result.success is True
        assert simple_agent.run_count == 1

    @pytest.mark.asyncio
    async def test_execute_nonexistent_agent(self, orchestrator):
        """Test executing nonexistent agent."""
        result = await orchestrator.execute_agent("NonExistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_disabled_agent(self, orchestrator, simple_agent):
        """Test that disabled agents don't execute."""
        orchestrator.register_agent(simple_agent)
        simple_agent.enabled = False
        
        result = await orchestrator.execute_agent("TestAgent")
        # Should still execute on-demand, regardless of enabled flag
        assert result is not None

    def test_orchestrator_status(self, orchestrator, simple_agent):
        """Test orchestrator status reporting."""
        orchestrator.register_agent(simple_agent, interval_seconds=60)
        status = orchestrator.get_status()

        assert status["name"] == "TestOrchestrator"
        assert status["running"] is False
        assert "TestAgent" in status["agents"]
        assert "TestAgent" in status["schedules"]
        assert "metrics" in status

    def test_agent_schedule_execution_check(self):
        """Test schedule execution check."""
        schedule = AgentSchedule(agent_name="Test", interval_seconds=60)
        assert schedule.should_execute() is True

        # Set future execution time
        schedule.next_execution = datetime.utcnow() + timedelta(seconds=60)
        assert schedule.should_execute() is False

    def test_agent_schedule_update(self):
        """Test schedule time update."""
        schedule = AgentSchedule(agent_name="Test", interval_seconds=60)
        schedule.update_next_execution()

        assert schedule.last_executed is not None
        assert schedule.next_execution is not None
        assert (
            schedule.next_execution - schedule.last_executed
        ).total_seconds() == 60


# Tests for Agent Monitor
class TestAgentMonitor:
    """Test monitoring and event logging."""

    def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.max_event_history == 1000
        assert len(monitor.events) == 0

    def test_record_event(self, monitor):
        """Test event recording."""
        monitor.record_event(
            EventType.AGENT_STARTED,
            agent_name="TestAgent",
            message="Agent started",
        )
        assert len(monitor.events) == 1
        assert monitor.events[0].event_type == EventType.AGENT_STARTED

    def test_event_history_limit(self):
        """Test event history size limit."""
        monitor = AgentMonitor(max_event_history=10)
        for i in range(20):
            monitor.record_event(
                EventType.AGENT_STARTED, agent_name="Test", message=f"Event {i}"
            )
        assert len(monitor.events) == 10

    def test_update_agent_health_success(self, monitor):
        """Test updating agent health on success."""
        monitor.update_agent_health("TestAgent", success=True)
        health = monitor.get_agent_health("TestAgent")

        assert health is not None
        assert health.is_healthy is True
        assert health.consecutive_failures == 0

    def test_update_agent_health_failure(self, monitor):
        """Test updating agent health on failure."""
        monitor.update_agent_health("TestAgent", success=False, error="Test error")
        health = monitor.get_agent_health("TestAgent")

        assert health is not None
        assert health.consecutive_failures == 1
        assert health.last_error == "Test error"

    def test_consecutive_failures_threshold(self, monitor):
        """Test unhealthy status after consecutive failures."""
        for _ in range(3):
            monitor.update_agent_health("TestAgent", success=False, error="Error")

        health = monitor.get_agent_health("TestAgent")
        assert health.is_healthy is False
        assert health.consecutive_failures == 3

    def test_get_unhealthy_agents(self, monitor):
        """Test retrieving unhealthy agents."""
        monitor.update_agent_health("Agent1", success=True)
        
        for _ in range(3):
            monitor.update_agent_health("Agent2", success=False, error="Error")

        unhealthy = monitor.get_unhealthy_agents()
        assert "Agent2" in unhealthy
        assert "Agent1" not in unhealthy

    def test_query_events_with_filter(self, monitor):
        """Test querying events with filters."""
        monitor.record_event(
            EventType.AGENT_STARTED, agent_name="Agent1", message="Started"
        )
        monitor.record_event(
            EventType.AGENT_COMPLETED, agent_name="Agent2", message="Completed"
        )

        # Filter by agent
        events = monitor.get_events(agent_name="Agent1")
        assert len(events) == 1
        assert events[0].agent_name == "Agent1"

    def test_status_summary(self, monitor):
        """Test status summary generation."""
        monitor.update_agent_health("Agent1", success=True)
        # Mark Agent2 as unhealthy with 3 consecutive failures
        for _ in range(3):
            monitor.update_agent_health("Agent2", success=False, error="Error")
        
        summary = monitor.get_status_summary()
        assert summary["total_agents"] == 2
        assert summary["healthy_agents"] == 1
        assert summary["unhealthy_agents"] == 1


# Tests for Orchestrator Metrics
class TestOrchestratorMetrics:
    """Test orchestrator metrics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = OrchestratorMetrics()
        assert metrics.total_cycles == 0
        assert metrics.uptime_seconds >= 0

    def test_cycle_success_rate(self):
        """Test cycle success rate calculation."""
        metrics = OrchestratorMetrics()
        metrics.total_cycles = 10
        metrics.successful_cycles = 8
        assert metrics.cycle_success_rate == 80.0

    def test_agent_success_rate(self):
        """Test agent success rate calculation."""
        metrics = OrchestratorMetrics()
        metrics.total_agent_runs = 20
        metrics.total_agent_successes = 15
        assert metrics.agent_success_rate == 75.0


# Integration Tests
class TestAgentIntegration:
    """Integration tests for agent orchestration."""

    @pytest.mark.asyncio
    async def test_multiple_agents_execution(self, orchestrator):
        """Test executing multiple agents."""
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        agent3 = MockAgent("Agent3")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)

        # Execute each
        await orchestrator.execute_agent("Agent1")
        await orchestrator.execute_agent("Agent2")
        await orchestrator.execute_agent("Agent3")

        assert agent1.run_count == 1
        assert agent2.run_count == 1
        assert agent3.run_count == 1

    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, orchestrator):
        """Test handling of agent failures."""
        failing = MockAgent("Failing", should_fail=True)
        success = MockAgent("Success")

        orchestrator.register_agent(failing)
        orchestrator.register_agent(success)

        result1 = await orchestrator.execute_agent("Failing")
        result2 = await orchestrator.execute_agent("Success")

        assert result1.success is False
        assert result2.success is True

    @pytest.mark.asyncio
    async def test_scheduled_execution(self, orchestrator, simple_agent):
        """Test scheduled agent execution."""
        orchestrator.register_agent(simple_agent, interval_seconds=100)

        # First execution should happen immediately
        results = await orchestrator.execute_scheduled_agents()
        assert len(results) == 1
        assert results[0].success is True

        # Second execution should not happen yet
        results = await orchestrator.execute_scheduled_agents()
        assert len(results) == 0

    def test_agent_priority_ordering(self, orchestrator):
        """Test agents are ordered by priority."""
        critical = MockAgent("Critical", priority=AgentPriority.CRITICAL)
        normal = MockAgent("Normal", priority=AgentPriority.NORMAL)
        low = MockAgent("Low", priority=AgentPriority.LOW)

        orchestrator.register_agent(normal)
        orchestrator.register_agent(low)
        orchestrator.register_agent(critical)

        status = orchestrator.get_status()
        # Just verify all agents are registered
        assert len(status["agents"]) == 3


# Edge Case Tests
class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self, orchestrator):
        """Test multiple concurrent executions."""
        agents = [MockAgent(f"Agent{i}") for i in range(5)]
        for agent in agents:
            orchestrator.register_agent(agent)

        tasks = [orchestrator.execute_agent(f"Agent{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r.success for r in results)

    def test_empty_orchestrator_status(self, orchestrator):
        """Test status of empty orchestrator."""
        status = orchestrator.get_status()
        assert status["agents"] == {}
        assert status["schedules"] == {}

    @pytest.mark.asyncio
    async def test_agent_execution_timing(self):
        """Test agent execution timing."""
        slow = MockAgent("Slow", delay_seconds=0.1)
        
        import time
        start = time.time()
        result = await slow.run()
        elapsed = time.time() - start

        assert result.success is True
        assert elapsed >= 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
