"""Sensor platform for the Nitrado integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MEMORY_SENSOR_GAMES
from .coordinator import NitradoAccountCoordinator, NitradoCoordinator
from .entity import account_device_info, service_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NitradoCoordinator = data["coordinator"]
    account_coordinator: NitradoAccountCoordinator = data["account_coordinator"]

    entities: list[SensorEntity] = []
    for service_id in coordinator.data:
        entities.append(NitradoStatusSensor(coordinator, service_id))
        entities.append(NitradoContractStatusSensor(coordinator, service_id))
        entities.append(NitradoExpiryDateSensor(coordinator, service_id))
        entities.append(NitradoPlayerCountSensor(coordinator, service_id))
        entities.append(NitradoMapSensor(coordinator, service_id))
        entities.append(NitradoVersionSensor(coordinator, service_id))
        entities.append(NitradoConnectAddressSensor(coordinator, service_id))

        game_human = (
            coordinator.data[service_id].get("gameserver", {}).get("game_human") or ""
        )
        if any(game in game_human.lower() for game in MEMORY_SENSOR_GAMES):
            entities.append(NitradoMemorySensor(coordinator, service_id))
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
        return self.coordinator.data.get(self._service_id, {}).get("gameserver", {})

    @property
    def native_value(self) -> str | None:
        return self._gameserver.get("status")

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoContractStatusSensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Contract status of a Nitrado service (active/suspended/...).

    Distinct from NitradoStatusSensor, which reflects the game process
    (online/offline) rather than the subscription itself.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "contract_status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_contract_status"

    @property
    def _contract(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._service_id, {}).get("contract", {})

    @property
    def native_value(self) -> str | None:
        return self._contract.get("status")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        details = self._contract.get("details", {})
        attributes = {
            "slots": details.get("slots"),
            "address": details.get("address"),
            "comment": self._contract.get("comment"),
            "delete_date": self._contract.get("delete_date"),
        }
        return {key: value for key, value in attributes.items() if value is not None}

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoExpiryDateSensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Date the service will be suspended unless renewed."""

    _attr_has_entity_name = True
    _attr_translation_key = "expiry_date"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_expiry_date"

    @property
    def native_value(self) -> datetime | None:
        contract = self.coordinator.data.get(self._service_id, {}).get("contract", {})
        suspend_date = contract.get("suspend_date")
        if not suspend_date:
            return None
        try:
            return datetime.fromisoformat(suspend_date).replace(tzinfo=dt_util.UTC)
        except ValueError:
            return None

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoPlayerCountSensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Current player count of a Nitrado game server.

    Not every game answers the query protocol, so `query` (and therefore
    this sensor's value) may legitimately be unavailable.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "player_count"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "players"

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_player_count"

    @property
    def _query(self) -> dict[str, Any]:
        gameserver = self.coordinator.data.get(self._service_id, {}).get("gameserver", {})
        return gameserver.get("query") or {}

    @property
    def native_value(self) -> int | None:
        return self._query.get("player_current")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attributes = {"max": self._query.get("player_max")}
        players = self._query.get("players")
        if players:
            attributes["players"] = [player.get("name") for player in players]
        return {key: value for key, value in attributes.items() if value is not None}

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoMapSensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Currently loaded map, if the game answers the query protocol."""

    _attr_has_entity_name = True
    _attr_translation_key = "map"

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_map"

    @property
    def native_value(self) -> str | None:
        gameserver = self.coordinator.data.get(self._service_id, {}).get("gameserver", {})
        query = gameserver.get("query") or {}
        return query.get("map")

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoVersionSensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Game/server version, if the game answers the query protocol."""

    _attr_has_entity_name = True
    _attr_translation_key = "version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_version"

    @property
    def native_value(self) -> str | None:
        gameserver = self.coordinator.data.get(self._service_id, {}).get("gameserver", {})
        query = gameserver.get("query") or {}
        return query.get("version")

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoConnectAddressSensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Connect address (IP:port) reported by the query protocol."""

    _attr_has_entity_name = True
    _attr_translation_key = "connect_address"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_connect_address"

    @property
    def native_value(self) -> str | None:
        gameserver = self.coordinator.data.get(self._service_id, {}).get("gameserver", {})
        query = gameserver.get("query") or {}
        return query.get("connect_ip")

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoMemorySensor(CoordinatorEntity[NitradoCoordinator], SensorEntity):
    """Allocated RAM, only added for games where that figure is meaningful.

    See MEMORY_SENSOR_GAMES: currently Minecraft and Hytale.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "memory"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_memory"

    @property
    def native_value(self) -> int | None:
        gameserver = self.coordinator.data.get(self._service_id, {}).get("gameserver", {})
        return gameserver.get("memory_mb")

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
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
