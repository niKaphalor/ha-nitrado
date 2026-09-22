"""Image platform for the Nitrado integration: account avatar."""
from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import DOMAIN
from .coordinator import NitradoAccountCoordinator
from .entity import account_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    account_coordinator: NitradoAccountCoordinator = hass.data[DOMAIN][entry.entry_id][
        "account_coordinator"
    ]
    async_add_entities([NitradoAvatarImage(hass, account_coordinator)])


class NitradoAvatarImage(CoordinatorEntity[NitradoAccountCoordinator], ImageEntity):
    """Profile picture of the Nitrado account."""

    _attr_has_entity_name = True
    _attr_translation_key = "avatar"

    def __init__(self, hass: HomeAssistant, coordinator: NitradoAccountCoordinator) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self._attr_unique_id = f"{coordinator.data.get('user_id')}_avatar"
        self._update_image_url()

    def _update_image_url(self) -> None:
        url = self.coordinator.data.get("avatar")
        if url != self._attr_image_url:
            self._attr_image_url = url
            self._attr_image_last_updated = utcnow()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_image_url()
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        return account_device_info(self.coordinator.data)
