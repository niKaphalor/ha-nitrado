"""The Nitrado integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NitradoApiClient
from .const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN
from .coordinator import NitradoAccountCoordinator, NitradoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.IMAGE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry: create client + coordinators, forward platforms."""
    session = async_get_clientsession(hass)
    client = NitradoApiClient(session, entry.data[CONF_API_TOKEN])

    service_ids = [int(sid) for sid in entry.options.get(CONF_SERVICES, [])]

    coordinator = NitradoCoordinator(hass, entry, client, service_ids)
    account_coordinator = NitradoAccountCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    await account_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "account_coordinator": account_coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change (e.g. a different server selection)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
