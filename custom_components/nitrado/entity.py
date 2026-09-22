"""Shared entity helpers for the Nitrado integration."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN


def account_device_info(user_data: dict[str, Any]) -> DeviceInfo:
    """Build the DeviceInfo shared by all account-level entities."""
    user_id = user_data.get("user_id")
    return DeviceInfo(
        identifiers={(DOMAIN, f"account_{user_id}")},
        name=user_data.get("username") or "Nitrado Account",
        manufacturer="Nitrado",
        entry_type=DeviceEntryType.SERVICE,
    )


def service_device_info(service_data: dict[str, Any], service_id: int) -> DeviceInfo:
    """Build the DeviceInfo shared by all entities of one Nitrado service.

    `service_data` is one coordinator.data[service_id] entry, i.e.
    {"gameserver": {...}, "contract": {...}}.
    """
    gameserver = service_data.get("gameserver", {})
    contract = service_data.get("contract", {})
    query = gameserver.get("query", {})
    name = query.get("server_name") or f"Nitrado {service_id}"
    model = contract.get("type_human") or gameserver.get("game_human")
    return DeviceInfo(
        identifiers={(DOMAIN, str(service_id))},
        name=name,
        manufacturer="Nitrado",
        model=model,
    )
