from collections import deque
from typing import Any

import aiohttp


class RegoService:
    """Queue NEVDIS lookups and send to API."""

    def __init__(self, config):
        self.config = config
        self.queue: deque[dict[str, Any]] = deque()

    def queue_lookup(self, sighting: dict):
        self.queue.append(sighting)

    def process_queue(self):
        """Process queued lookups sequentially."""
        if not self.queue:
            return

        # Non-async placeholder to keep interface simple here
        sighting = self.queue.popleft()
        return self._send_lookup_sync(sighting)

    def _send_lookup_sync(self, sighting: dict):
        """Blocking HTTP call for now; replace with asyncio loop if needed."""
        import asyncio

        async def _send():
            url = f"{self.config.api_base_url}/api/plates"
            headers = {"X-API-Key": self.config.api_key}
            async with aiohttp.ClientSession() as session, session.post(
                url, json=sighting, headers=headers
            ) as resp:
                return await resp.json()

        return asyncio.get_event_loop().run_until_complete(_send())
