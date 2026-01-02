import aiohttp


class AlertService:
    """Send alerts to Cloudflare API."""

    def __init__(self, config):
        self.config = config

    async def send_face_sighting(self, payload: dict):
        """Send face sighting to API."""
        url = f"{self.config.api_base_url}/api/faces"
        headers = {"X-API-Key": self.config.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                return await resp.json()
