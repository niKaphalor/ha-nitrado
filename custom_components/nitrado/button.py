"""Button platform for the Nitrado integration: server power controls."""
from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import NitradoApiError
from .const import DOMAIN
from .coordinator import NitradoCoordinator
from .entity import service_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NitradoCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[ButtonEntity] = []
    for service_id in coordinator.data:
        entities.append(NitradoStartButton(coordinator, service_id))
        entities.append(NitradoStopButton(coordinator, service_id))
        entities.append(NitradoRestartButton(coordinator, service_id))
    async_add_entities(entities)


class _NitradoServiceButton(CoordinatorEntity[NitradoCoordinator], ButtonEntity):
    """Shared base for the per-service power control buttons."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator)
        self._service_id = service_id

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )


class NitradoStartButton(_NitradoServiceButton):
    """Start the game server.

    Nitrado has no separate start endpoint: restart also starts a
    currently stopped server, so this calls the same API method as
    NitradoRestartButton.
    """

    _attr_translation_key = "start"

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator, service_id)
        self._attr_unique_id = f"{service_id}_start"

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_restart_gameserver(self._service_id)
        except NitradoApiError as err:
            raise HomeAssistantError(f"Could not start server: {err}") from err
        await self.coordinator.async_request_refresh()


class NitradoStopButton(_NitradoServiceButton):
    """Stop the game server."""

    _attr_translation_key = "stop"

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator, service_id)
        self._attr_unique_id = f"{service_id}_stop"

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_stop_gameserver(self._service_id)
        except NitradoApiError as err:
            raise HomeAssistantError(f"Could not stop server: {err}") from err
        await self.coordinator.async_request_refresh()


class NitradoRestartButton(_NitradoServiceButton):
    """Restart the game server."""

    _attr_translation_key = "restart"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, coordinator: NitradoCoordinator, service_id: int) -> None:
        super().__init__(coordinator, service_id)
        self._attr_unique_id = f"{service_id}_restart"

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_restart_gameserver(self._service_id)
        except NitradoApiError as err:
            raise HomeAssistantError(f"Could not restart server: {err}") from err
        await self.coordinator.async_request_refresh()
