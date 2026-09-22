"""Sensor platform for the Nitrado integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NitradoAccountCoordinator, NitradoCoordinator
from .entity import account_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NitradoCoordinator = data["coordinator"]
    account_coordinator: NitradoAccountCoordinator = data["account_coordinator"]

    entities: list[SensorEntity] = [
        NitradoStatusSensor(coordinator, service_id) for service_id in coordinator.data
    ]
    entities.extend(
        [
            NitradoAccountCreditSensor(account_coordinator),
            NitradoAccountUserIdSensor(account_coordinator),
            NitradoAccountUsernameSensor(account_coordinator),
        ]
    )
    async_add_entities(entities)


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


class NitradoAccountCreditSensor(CoordinatorEntity[NitradoAccountCoordinator], SensorEntity):
    """Current credit balance of the Nitrado account."""

    _attr_has_entity_name = True
    _attr_translation_key = "credit"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: NitradoAccountCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('user_id')}_credit"

    @property
    def native_value(self) -> float | None:
        credit = self.coordinator.data.get("credit")
        return credit / 100 if credit is not None else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.coordinator.data.get("currency")

    @property
    def device_info(self) -> DeviceInfo:
        return account_device_info(self.coordinator.data)


class NitradoAccountUserIdSensor(CoordinatorEntity[NitradoAccountCoordinator], SensorEntity):
    """Nitrado user ID of the account."""

    _attr_has_entity_name = True
    _attr_translation_key = "user_id"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoAccountCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('user_id')}_user_id"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("user_id")

    @property
    def device_info(self) -> DeviceInfo:
        return account_device_info(self.coordinator.data)


class NitradoAccountUsernameSensor(CoordinatorEntity[NitradoAccountCoordinator], SensorEntity):
    """Username of the Nitrado account."""

    _attr_has_entity_name = True
    _attr_translation_key = "username"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoAccountCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('user_id')}_username"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("username")

    @property
    def device_info(self) -> DeviceInfo:
        return account_device_info(self.coordinator.data)
