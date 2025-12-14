"""Graceful shutdown and signal handling utilities.

Provides coordinated shutdown of services and agents with proper
cleanup and connection draining.
"""

import asyncio
import signal
from typing import Callable, List, Optional
from loguru import logger


class ShutdownHandler:
    """Manages graceful application shutdown.
    
    Coordinates shutdown of services:
    - Signals all handlers to stop accepting new work
    - Waits for in-flight operations to complete
    - Closes database and HTTP connections
    - Logs shutdown events
    """
    
    def __init__(self, timeout_seconds: int = 30) -> None:
        """Initialize shutdown handler.
        
        Args:
            timeout_seconds: Maximum time to wait for graceful shutdown
        """
        self.timeout_seconds = timeout_seconds
        self.shutdown_event = asyncio.Event()
        self.handlers: List[Callable] = []
        self.is_shutting_down = False
        logger.info(f"Initialized ShutdownHandler (timeout={timeout_seconds}s)")
    
    def register_shutdown_handler(self, handler: Callable) -> None:
        """Register a callback to be called during shutdown.
        
        Handlers are called in reverse order of registration.
        
        Args:
            handler: Async callable that performs cleanup
        """
        self.handlers.append(handler)
        logger.debug(f"Registered shutdown handler: {handler.__name__}")
    
    async def handle_shutdown(self) -> None:
        """Execute all registered shutdown handlers.
        
        Calls handlers in reverse registration order, imitating
        a stack-based cleanup pattern.
        """
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress, ignoring request")
            return
        
        self.is_shutting_down = True
        logger.info("Initiating graceful shutdown...")
        
        # Call handlers in reverse order
        for handler in reversed(self.handlers):
            try:
                logger.info(f"Running shutdown handler: {handler.__name__}")
                if asyncio.iscoroutinefunction(handler):
                    await asyncio.wait_for(
                        handler(),
                        timeout=self.timeout_seconds
                    )
                else:
                    handler()
                logger.debug(f"Shutdown handler completed: {handler.__name__}")
            except asyncio.TimeoutError:
                logger.error(f"Shutdown handler timeout: {handler.__name__}")
            except Exception as e:
                logger.error(f"Error in shutdown handler {handler.__name__}: {e}")
        
        self.shutdown_event.set()
        logger.info("Graceful shutdown completed")
    
    async def wait_for_shutdown(self) -> None:
        """Wait until shutdown is triggered."""
        await self.shutdown_event.wait()


class SignalHandler:
    """Handles OS signals for graceful shutdown.
    
    Converts OS signals (SIGTERM, SIGINT) into coordinated
    application shutdown.
    """
    
    def __init__(self, shutdown_handler: ShutdownHandler) -> None:
        """Initialize signal handler.
        
        Args:
            shutdown_handler: ShutdownHandler instance to trigger
        """
        self.shutdown_handler = shutdown_handler
        logger.info("Initialized SignalHandler")
    
    def setup(self, loop: asyncio.AbstractEventLoop) -> None:
        """Setup signal handlers for the event loop.
        
        Args:
            loop: Event loop to register handlers with
        """
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(
                        self._signal_handler(s)
                    )
                )
                logger.debug(f"Registered signal handler for {sig.name}")
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                logger.warning(f"Signal handler not available on this platform for {sig.name}")
    
    async def _signal_handler(self, sig: signal.Signals) -> None:
        """Handle OS signal.
        
        Args:
            sig: Signal that was received
        """
        logger.warning(f"Received signal {sig.name}, initiating shutdown...")
        await self.shutdown_handler.handle_shutdown()
