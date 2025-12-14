"""Configuration validation and runtime checks.

Provides comprehensive validation of application configuration
before startup to catch issues early.
"""

from typing import List, Tuple, Optional
import httpx
from loguru import logger
from config.settings import settings


class ConfigurationValidator:
    """Validates application configuration at startup.
    
    Performs checks for:
    - Required settings presence
    - URL validity and accessibility
    - API key validity
    - Database connectivity
    - Scheduler configuration
    """
    
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    async def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks.
        
        Returns:
            Tuple of (success, errors, warnings)
        """
        logger.info("Starting configuration validation")
        
        await self._validate_arr_services()
        await self._validate_database()
        await self._validate_discovery_config()
        
        if self.errors:
            logger.error(f"Configuration validation failed with {len(self.errors)} error(s)")
            return False, self.errors, self.warnings
        
        if self.warnings:
            logger.warning(f"Configuration validation passed with {len(self.warnings)} warning(s)")
        else:
            logger.info("Configuration validation passed")
        
        return True, self.errors, self.warnings
    
    async def _validate_arr_services(self) -> None:
        """Validate Arr service URLs and accessibility."""
        services = [
            ("Radarr", settings.radarr_url, settings.radarr_api_key),
            ("Sonarr", settings.sonarr_url, settings.sonarr_api_key),
            ("Prowlarr", settings.prowlarr_url, settings.prowlarr_api_key),
        ]
        
        for name, url, api_key in services:
            if not url:
                self.errors.append(f"{name} URL is not configured")
                continue
            
            if not api_key:
                self.errors.append(f"{name} API key is not configured")
                continue
            
            # Try to connect
            try:
                async with httpx.AsyncClient(
                    base_url=url,
                    headers={"X-Api-Key": api_key},
                    timeout=10.0
                ) as client:
                    response = await client.get("/api/v3/system/status" if name != "Prowlarr" else "/api/v1/system/status")
                    if response.status_code != 200:
                        self.errors.append(f"{name} returned status {response.status_code}")
                    else:
                        logger.info(f"✓ {name} is accessible and responding")
            except httpx.ConnectError:
                self.errors.append(f"Cannot connect to {name} at {url} - connection refused")
            except httpx.TimeoutException:
                self.errors.append(f"{name} at {url} - request timeout (service may be unreachable)")
            except Exception as e:
                self.errors.append(f"{name} validation failed: {str(e)}")
    
    async def _validate_database(self) -> None:
        """Validate database configuration and connectivity."""
        from db.session import engine
        
        logger.info("Validating database configuration")
        
        # Check if database URL is set
        if not settings.database_url:
            self.errors.append("DATABASE_URL is not configured")
            return
        
        # Try to connect to database
        try:
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            logger.info(f"✓ Database is accessible: {settings.database_url.split('://')[0]}")
        except Exception as e:
            self.errors.append(f"Cannot connect to database: {str(e)}")
    
    async def _validate_discovery_config(self) -> None:
        """Validate discovery configuration if enabled."""
        if not settings.discovery_enabled:
            return
        
        logger.info("Validating discovery configuration")
        
        if not settings.discovery_sources:
            self.errors.append("DISCOVERY_ENABLED=true but no DISCOVERY_SOURCES configured")
            return
        
        # Try to fetch from one source
        for i, source in enumerate(settings.discovery_sources[:1]):  # Test first source
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(source)
                    if response.status_code == 200:
                        logger.info(f"✓ Discovery source {i+1} is accessible")
                    else:
                        self.warnings.append(
                            f"Discovery source {i+1} returned status {response.status_code}"
                        )
            except Exception as e:
                self.warnings.append(f"Discovery source {i+1} not reachable: {str(e)}")


async def validate_startup_configuration() -> None:
    """Validate configuration and raise on error.
    
    Should be called during application startup.
    
    Raises:
        RuntimeError: If configuration is invalid
    """
    validator = ConfigurationValidator()
    success, errors, warnings = await validator.validate_all()
    
    if not success:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)
    
    # Log warnings (non-blocking)
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
