from typing import Any

from core.logging import logger
from db.session import SessionLocal
from db.models import IndexerHealth


class IndexerAutoHealAgent:
    """Agent that monitors indexer health, records results, and auto-disables failing indexers.

    This is the main healing automation agent, running periodically (e.g., every 2 hours).
    On each run:
    1. Tests all indexers in Radarr and Sonarr
    2. Records results in the database
    3. Automatically disables any indexer that fails the test
    """

    def __init__(self, radarr: Any, sonarr: Any, control_agent: Any) -> None:
        self.radarr = radarr
        self.sonarr = sonarr
        self.control = control_agent

    async def run(self) -> None:
        """Execute autoheal cycle: test indexers, log results, disable failures."""
        logger.info("Autoheal cycle started")
        async with SessionLocal() as session:
            for service_name, service in [
                ("radarr", self.radarr),
                ("sonarr", self.sonarr),
            ]:
                try:
                    indexers = await service.get_indexers()
                except Exception:
                    logger.exception("Failed to fetch %s indexers during autoheal", service_name)
                    continue

                for idx in indexers:
                    indexer_name = idx.get("name", f"id={idx.get('id')}")
                    try:
                        await service.test_indexer(idx["id"])
                        session.add(
                            IndexerHealth(
                                service=service_name,
                                indexer_id=idx["id"],
                                name=indexer_name,
                                success=True,
                                error=None,
                            )
                        )
                        logger.debug("Indexer %s/%s passed health check", service_name, indexer_name)
                    except Exception as e:
                        error_msg = str(e)
                        session.add(
                            IndexerHealth(
                                service=service_name,
                                indexer_id=idx["id"],
                                name=indexer_name,
                                success=False,
                                error=error_msg,
                            )
                        )
                        logger.warning(
                            "Indexer %s/%s failed health check: %s",
                            service_name,
                            indexer_name,
                            error_msg,
                        )
                        try:
                            await self.control.disable_indexer(service, idx)
                        except Exception:
                            logger.exception(
                                "Failed to disable indexer %s/%s",
                                service_name,
                                indexer_name,
                            )

            try:
                await session.commit()
                logger.info("Autoheal cycle completed successfully")
            except Exception:
                logger.exception("Failed to commit autoheal results to database")
                await session.rollback()
