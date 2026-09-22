"""Thin async wrapper around the Nitrado REST API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15


class NitradoApiError(Exception):
    """Generic error while talking to the Nitrado API."""


class NitradoAuthError(NitradoApiError):
    """Raised when the token is invalid or expired (HTTP 401/403)."""


class NitradoConnectionError(NitradoApiError):
    """Raised when the Nitrado API could not be reached (timeout, DNS, etc.)."""


class NitradoApiClient:
    """Wraps the Nitrado endpoints this integration needs."""

    def __init__(self, session: aiohttp.ClientSession, api_token: str) -> None:
        self._session = session
        self._headers = {"Authorization": f"Bearer {api_token}"}

    async def _request(self, path: str) -> dict[str, Any]:
        url = f"{API_BASE_URL}{path}"
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(url, headers=self._headers)
        except (TimeoutError, aiohttp.ClientError) as err:
            raise NitradoConnectionError(f"Failed to connect to {url}") from err

        if response.status in (401, 403):
            raise NitradoAuthError("Nitrado API token is invalid or expired")
        if response.status != 200:
            body = await response.text()
            raise NitradoApiError(f"Unexpected status {response.status} from {url}: {body}")

        payload = await response.json()
        if payload.get("status") != "success":
            raise NitradoApiError(f"Nitrado reported an error: {payload}")
        return payload["data"]

    async def async_get_services(self) -> list[dict[str, Any]]:
        """Return all services (servers) in the Nitrado account."""
        data = await self._request("/services")
        return data.get("services", [])

    async def async_get_gameserver(self, service_id: int) -> dict[str, Any]:
        """Return live data (status, players, ...) for a single server."""
        data = await self._request(f"/services/{service_id}/gameservers")
        return data.get("gameserver", {})

    async def async_get_service(self, service_id: int) -> dict[str, Any]:
        """Return contract data (status, expiry date, ...) for a single service."""
        data = await self._request(f"/services/{service_id}")
        return data.get("service", {})

    async def async_get_user(self) -> dict[str, Any]:
        """Return account information for the authenticated user."""
        data = await self._request("/user")
        return data.get("user", {})
