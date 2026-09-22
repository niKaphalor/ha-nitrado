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


# Preference order when picking an icon size from a game catalog entry's
# `icons` object (largest first).
_ICON_SIZE_PREFERENCE = ("x256", "x120", "x64", "x32", "x16")


def resolve_game_icon(
    game_icons: dict[str, dict[str, str]], service_data: dict[str, Any]
) -> str | None:
    """Look up a service's game icon URL in the games catalog.

    `game_icons` maps a game's `folder_short` to its `icons` object (as
    returned by GET /gameserver/games); `service_data` is one
    coordinator.data[service_id] entry.
    """
    details = service_data.get("contract", {}).get("details", {})
    folder_short = details.get("folder_short")
    if not folder_short:
        return None
    icons = game_icons.get(folder_short, {})
    for size in _ICON_SIZE_PREFERENCE:
        if icons.get(size):
            return icons[size]
    return None
