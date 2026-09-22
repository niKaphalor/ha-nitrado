"""Binary sensor platform for the Nitrado integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NitradoCoordinator
from .entity import service_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NitradoCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = []
    for service_id in coordinator.data:
        entities.append(NitradoAutoExtensionBinarySensor(coordinator, service_id))
        entities.append(NitradoMustBeStartedBinarySensor(coordinator, service_id))
    async_add_entities(entities)


class NitradoAutoExtensionBinarySensor(CoordinatorEntity[NitradoCoordinator], BinarySensorEntity):
    """Whether a Nitrado service renews itself automatically."""

    _attr_has_entity_name = True
    _attr_translation_key = "auto_extension"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_auto_extension"

    @property
    def is_on(self) -> bool | None:
        contract = self.coordinator.data.get(self._service_id, {}).get("contract", {})
        return contract.get("auto_extension")

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoMustBeStartedBinarySensor(CoordinatorEntity[NitradoCoordinator], BinarySensorEntity):
    """Whether the server is configured to be running (admin intent).

    Distinct from the "Status" sensor, which reflects whether the game
    process is actually online. A server that "must be started" but whose
    status isn't "started" points at a problem worth looking into.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "must_be_started"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id
        self._attr_unique_id = f"{service_id}_must_be_started"

    @property
    def is_on(self) -> bool | None:
        gameserver = self.coordinator.data.get(self._service_id, {}).get("gameserver", {})
        return gameserver.get("must_be_started")

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )
