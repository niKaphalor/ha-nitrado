"""Image platform for the Nitrado integration: account avatar, game icons."""
from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import DOMAIN
from .coordinator import NitradoAccountCoordinator, NitradoCoordinator
from .entity import account_device_info, resolve_game_icon, service_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    account_coordinator: NitradoAccountCoordinator = data["account_coordinator"]
    coordinator: NitradoCoordinator = data["coordinator"]
    game_icons: dict[str, dict[str, str]] = data["game_icons"]

    entities: list[ImageEntity] = [NitradoAvatarImage(hass, account_coordinator)]
    for service_id, service_data in coordinator.data.items():
        if resolve_game_icon(game_icons, service_data):
            entities.append(NitradoGameIconImage(hass, coordinator, service_id, game_icons))
    async_add_entities(entities)


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
            # entity_picture only appears once image_last_updated is set, so
            # leave it unset (None) when there's no URL instead of exposing
            # a proxy link that would just fail to fetch.
            self._attr_image_last_updated = utcnow() if url else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_image_url()
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        return account_device_info(self.coordinator.data)


class NitradoGameIconImage(CoordinatorEntity[NitradoCoordinator], ImageEntity):
    """Icon of the game running on a service, from Nitrado's game catalog."""

    _attr_has_entity_name = True
    _attr_translation_key = "game_icon"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: NitradoCoordinator,
        service_id: int,
        game_icons: dict[str, dict[str, str]],
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self._service_id = service_id
        self._game_icons = game_icons
        self._attr_unique_id = f"{service_id}_game_icon"
        self._update_image_url()

    def _update_image_url(self) -> None:
        url = resolve_game_icon(
            self._game_icons, self.coordinator.data.get(self._service_id, {})
        )
        if url != self._attr_image_url:
            self._attr_image_url = url
            self._attr_image_last_updated = utcnow() if url else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_image_url()
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        return service_device_info(
            self.coordinator.data.get(self._service_id, {}), self._service_id
        )
