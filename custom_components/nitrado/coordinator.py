"""DataUpdateCoordinator for the Nitrado integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NitradoApiClient, NitradoApiError, NitradoAuthError
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class NitradoCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Polls all configured Nitrado services in one place.

    One coordinator per config entry (= per Nitrado account), so entities
    don't poll individually and we respect Nitrado's rate limit.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: NitradoApiClient,
        service_ids: list[int],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Nitrado",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self._service_ids = service_ids

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Poll all services. A single failure must not break the rest."""
        results: dict[int, dict[str, Any]] = {}
        for service_id in self._service_ids:
            try:
                results[service_id] = await self.client.async_get_gameserver(service_id)
            except NitradoAuthError as err:
                # Token invalid -> HA will automatically show a reauth prompt
                raise UpdateFailed(str(err)) from err
            except NitradoApiError as err:
                _LOGGER.warning("Could not fetch service %s: %s", service_id, err)
                results[service_id] = {}
        return results
