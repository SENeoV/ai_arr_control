"""Indexer discovery agent.

Fetches candidate indexer lists from configured discovery sources and
optionally adds them to Prowlarr. Discovery sources are expected to return
either a JSON array of indexer objects or a plain text list of base URLs.

This agent is conservative by default (must enable `discovery_add_to_prowlarr`
in settings to allow automatic adds).
"""
from typing import Any, List, Dict
import json
import httpx
from loguru import logger

from config.settings import settings
from agents.base import Agent, AgentResult, AgentPriority


class IndexerDiscoveryAgent(Agent):
    """Agent that discovers potential indexers from external sources.

    Args:
        prowlarr_service: ProwlarrService instance (optional)
    """

    def __init__(self, prowlarr_service: Any = None) -> None:
        super().__init__(
            name="IndexerDiscoveryAgent",
            priority=AgentPriority.LOW,
            enabled=settings.discovery_enabled,
        )
        self.prowlarr = prowlarr_service
        logger.info("Initialized IndexerDiscoveryAgent")

    async def run(self) -> AgentResult:
        """Run discovery against all configured sources.
        
        Returns:
            AgentResult with discovery metrics and status
        """
        if not settings.discovery_enabled:
            logger.info("Discovery is disabled in settings; skipping")
            return AgentResult(
                success=True,
                message="Discovery disabled in configuration"
            )

        sources = settings.discovery_sources or []
        if not sources:
            logger.info("No discovery sources configured; skipping")
            return AgentResult(
                success=True,
                message="No discovery sources configured"
            )

        logger.info(f"Running indexer discovery against {len(sources)} sources")
        
        total_discovered = 0
        failed_sources = 0

        for src in sources:
            try:
                discovered = await self._process_source(src)
                total_discovered += discovered
            except Exception as e:
                logger.error(f"Error processing discovery source {src}: {e}")
                failed_sources += 1

        message = f"Discovery complete: {total_discovered} indexers found"
        success = failed_sources == 0 if sources else True
        
        return AgentResult(
            success=success,
            message=message,
            metrics={
                "total_discovered": total_discovered,
                "sources_processed": len(sources) - failed_sources,
                "failed_sources": failed_sources,
            },
            error=f"{failed_sources} sources failed" if failed_sources > 0 else None
        )

    async def _process_source(self, url: str) -> int:
        """Process a discovery source and return count of discovered indexers."""
        logger.debug(f"Fetching discovery source: {url}")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            text = resp.text

            candidates: List[dict] = []

            # Try JSON
            try:
                data = resp.json()
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            candidates.append(item)
                        elif isinstance(item, str):
                            candidates.append({"baseUrl": item})
                elif isinstance(data, dict):
                    # single object may contain list under a key
                    for v in data.values():
                        if isinstance(v, list):
                            for it in v:
                                if isinstance(it, dict):
                                    candidates.append(it)
                # else ignore
            except (ValueError, json.JSONDecodeError):
                # fallback: parse as newline-separated text of URLs
                for line in text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    candidates.append({"baseUrl": line})

            logger.info(f"Discovered {len(candidates)} candidate indexers from {url}")

            # Optionally add to Prowlarr
            if settings.discovery_add_to_prowlarr and self.prowlarr:
                await self._add_to_prowlarr(candidates)
            
            return len(candidates)

    async def _add_to_prowlarr(self, candidates: List[dict]) -> None:
        for c in candidates:
            try:
                # Expecting Prowlarr-compatible indexer object; best-effort POST
                logger.info(f"Adding discovered indexer to Prowlarr: {c.get('baseUrl') or c.get('name')}")
                await self.prowlarr.client.post("/api/v1/indexer", json=c)
            except Exception as e:
                logger.error(f"Failed to add discovered indexer {c}: {e}")
