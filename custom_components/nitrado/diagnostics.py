"""Diagnostics support for the Nitrado integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_TOKEN, DOMAIN
from .coordinator import NitradoAccountCoordinator, NitradoCoordinator

# Access tokens, device credentials (FTP/MySQL passwords), and the account's
# email/postal address must never end up in a diagnostics dump that gets
# attached to a public GitHub issue.
TO_REDACT = {
    CONF_API_TOKEN,
    "websocket_token",
    "credentials",
    "email",
    "profile",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NitradoCoordinator = data["coordinator"]
    account_coordinator: NitradoAccountCoordinator = data["account_coordinator"]

    return async_redact_data(
        {
            "entry_data": dict(entry.data),
            "entry_options": dict(entry.options),
            "account": account_coordinator.data,
            "services": coordinator.data,
        },
        TO_REDACT,
    )
