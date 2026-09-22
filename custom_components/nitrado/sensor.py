"""Sensor platform for the Nitrado integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NitradoCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NitradoCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        NitradoStatusSensor(coordinator, service_id) for service_id in coordinator.data
    )


class NitradoStatusSensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Online/offline status of a single Nitrado game server."""

    _attr_has_entity_name = True
    _attr_translation_key = "status"

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_status"

    @property
    def _gameserver(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._service_id, {})

    @property
    def native_value(self) -> str | None:
        return self._gameserver.get("status")

    @property
    def device_info(self) -> DeviceInfo:
        query = self._gameserver.get("query", {})
        name = query.get("server_name") or f"Nitrado {self._service_id}"
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._service_id))},
            name=name,
            manufacturer="Nitrado",
            model=self._gameserver.get("game_human"),
        )
