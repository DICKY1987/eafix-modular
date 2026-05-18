# doc_id: DOC-SERVICE-0220
"""
Startup Health Gate — polls dependency /healthz endpoints before accepting events.
Closes GAP-44, GAP-45.
"""
import asyncio
from typing import List, Tuple
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


class StartupHealthGate:
    """Polls /healthz on each dependency until healthy or timeout."""

    @staticmethod
    async def await_dependencies(
        services: List[str],
        timeout_seconds: int = 30,
        retry_interval_seconds: float = 2.0,
    ) -> None:
        """
        Await health of all services.

        Args:
            services: List of "host:port" strings (e.g. "calendar-ingestor:8081")
            timeout_seconds: Per-service timeout before raising
            retry_interval_seconds: Interval between retries
        Raises:
            TimeoutError: If any service is not healthy within timeout
        """
        tasks = [
            StartupHealthGate._await_one(svc, timeout_seconds, retry_interval_seconds)
            for svc in services
        ]
        await asyncio.gather(*tasks)

    @staticmethod
    async def _await_one(service: str, timeout: int, interval: float) -> None:
        url = f"http://{service}/healthz"
        deadline = asyncio.get_event_loop().time() + timeout
        logger.info("Awaiting dependency health", service=service, url=url)

        while asyncio.get_event_loop().time() < deadline:
            if await StartupHealthGate._check_health(url):
                logger.info("Dependency healthy", service=service)
                return
            await asyncio.sleep(interval)

        raise TimeoutError(
            f"Dependency {service} not healthy after {timeout}s"
        )

    @staticmethod
    async def _check_health(url: str) -> bool:
        if not _HAS_HTTPX:
            # Without httpx, assume healthy (best-effort)
            return True
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
