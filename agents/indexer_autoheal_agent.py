"""Autoheal agent for automatic indexer remediation.

The main autonomous agent that monitors indexer health, records results,
and automatically disables failing indexers to prevent service degradation.
"""

from typing import Any
from loguru import logger
from db.session import SessionLocal
from db.models import IndexerHealth


class IndexerAutoHealAgent:
    """Agent that monitors indexer health and automatically disables failures.
    
    This is the main autonomous healing agent. On each execution cycle, it:
    1. Tests all indexers in Radarr and Sonarr
    2. Records results in the database for auditing and trending
    3. Automatically disables any indexer that fails the health check
    4. Logs all actions for monitoring and debugging
    
    This agent makes actual changes to indexer state and should be
    configured with appropriate logging and alerting.
    
    Args:
        radarr: RadarrService instance
        sonarr: SonarrService instance
        control_agent: IndexerControlAgent instance for state changes
    """

    def __init__(self, radarr: Any, sonarr: Any, control_agent: Any) -> None:
        self.radarr = radarr
        self.sonarr = sonarr
        self.control = control_agent
        logger.info("Initialized IndexerAutoHealAgent")

    async def run(self) -> None:
        """Execute autoheal cycle: test indexers, log results, disable failures.
        
        This method is called periodically (e.g., every 2 hours) by the
        application scheduler. It performs the complete heal cycle atomically,
        committing all database changes at the end.
        
        Failures in individual indexer tests do not stop the cycle; all
        indexers are tested and results are recorded regardless.
        """
        logger.info("Starting autoheal cycle")
        
        async with SessionLocal() as session:
            total_tested = 0
            total_passed = 0
            total_failed = 0
            total_disabled = 0
            
            for service_name, service in [
                ("radarr", self.radarr),
                ("sonarr", self.sonarr),
            ]:
                try:
                    indexers = await service.get_indexers()
                except Exception as e:
                    logger.error(f"Failed to fetch {service_name} indexers: {e}")
                    continue

                logger.debug(f"Testing {len(indexers)} {service_name} indexers")
                
                for idx in indexers:
                    total_tested += 1
                    indexer_id = idx.get("id")
                    indexer_name = idx.get("name", f"unknown (id={indexer_id})")
                    
                    try:
                        await service.test_indexer(indexer_id)
                        
                        # Record successful test
                        session.add(
                            IndexerHealth(
                                service=service_name,
                                indexer_id=indexer_id,
                                name=indexer_name,
                                success=True,
                                error=None,
                            )
                        )
                        logger.debug(f"{service_name}/{indexer_name} passed health check")
                        total_passed += 1
                        
                    except Exception as e:
                        error_msg = str(e)[:200]  # Truncate long error messages
                        total_failed += 1
                        
                        # Record failed test
                        session.add(
                            IndexerHealth(
                                service=service_name,
                                indexer_id=indexer_id,
                                name=indexer_name,
                                success=False,
                                error=error_msg,
                            )
                        )
                        logger.warning(
                            f"{service_name}/{indexer_name} failed health check: {error_msg}"
                        )
                        
                        # Attempt to disable the failing indexer
                        try:
                            await self.control.disable_indexer(service, idx)
                            total_disabled += 1
                        except Exception as disable_error:
                            logger.error(
                                f"Failed to disable {service_name}/{indexer_name}: {disable_error}"
                            )

            # Commit all database changes
            try:
                await session.commit()
                logger.info(
                    f"Autoheal cycle completed: {total_tested} tested, "
                    f"{total_passed} passed, {total_failed} failed, "
                    f"{total_disabled} disabled"
                )
            except Exception as e:
                logger.error(f"Failed to commit autoheal results to database: {e}")
                await session.rollback()
