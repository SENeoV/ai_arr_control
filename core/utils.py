"""Utility functions for error handling, retry logic, and resilience."""

import asyncio
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
from loguru import logger

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator to retry async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for each retry
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorated async function that retries on failure
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator


class CircuitBreaker:
    """Simple circuit breaker pattern for handling cascading failures.
    
    Tracks failures and opens the circuit after a threshold to prevent
    hammering failing services.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False
    
    def record_success(self) -> None:
        """Record a successful call."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        try:
            self.last_failure_time = asyncio.get_running_loop().time()
        except RuntimeError:
            # No event loop running, use time.time()
            import time
            self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker '{self.name}' opened after {self.failure_count} failures")
    
    def can_proceed(self) -> bool:
        """Check if the circuit breaker allows proceeding."""
        if not self.is_open:
            return True
        
        # Try to recover after timeout
        if self.last_failure_time:
            try:
                current_time = asyncio.get_running_loop().time()
            except RuntimeError:
                # No event loop, use time.time()
                import time
                current_time = time.time()
            
            elapsed = current_time - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                logger.info(f"Circuit breaker '{self.name}' attempting recovery")
                self.is_open = False
                self.failure_count = 0
                return True
        
        return False


def validate_response(response: Any, required_keys: Optional[list] = None) -> bool:
    """Validate API response structure.
    
    Args:
        response: Response data to validate
        required_keys: List of keys that must be present
        
    Returns:
        True if response is valid
        
    Raises:
        ValueError: If response is invalid
    """
    if response is None:
        raise ValueError("Response is None")
    
    if isinstance(response, dict) and required_keys:
        missing = [k for k in required_keys if k not in response]
        if missing:
            raise ValueError(f"Response missing required keys: {missing}")
    
    return True
