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
