"""Tests for the per-service game icon, resolved via the games catalog."""
from unittest.mock import patch

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nitrado.const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN

# Trimmed example GET /gameserver/games payload as documented by Nitrado.
GAMES_CATALOG = [
    {
        "id": 1245,
        "name": "Ark: Survival Ascended",
        "folder_short": "arksa",
        "icons": {
            "x256": "https://assets.nitrado.net/gameicons/256/arksa.jpg",
            "x120": "https://assets.nitrado.net/gameicons/120/arksa.jpg",
            "x64": "https://assets.nitrado.net/gameicons/64/arksa.jpg",
            "x32": "https://assets.nitrado.net/gameicons/32/arksa.jpg",
            "x16": "https://assets.nitrado.net/gameicons/16/arksa.jpg",
        },
    },
    {
        "id": 265,
        "name": "Minecraft (Technic Platform)",
        "folder_short": "minecrafttekkit",
        "icons": {
            "x256": "https://assets.nitrado.net/gameicons/256/minecrafttekkit.jpg",
            "x120": "https://assets.nitrado.net/gameicons/120/minecrafttekkit.jpg",
        },
    },
    {
        # A catalog entry missing icons entirely should just be skipped.
        "id": 999,
        "name": "No Icons Game",
        "folder_short": "noicons",
        "icons": {},
    },
]

SERVICES_DATA = [
    {
        "id": 1,
        "status": "active",
        "auto_extension": True,
        "details": {"folder_short": "arksa"},
    },
    {
        "id": 2,
        "status": "active",
        "auto_extension": True,
        "details": {"folder_short": "unknown-folder"},
    },
    {
        "id": 3,
        "status": "active",
        "auto_extension": True,
        "details": {"folder_short": "noicons"},
    },
]

GAMESERVER_DATA = {"status": "started"}


async def _setup_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "test-token"},
        options={CONF_SERVICES: [1, 2, 3]},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_user",
        return_value={"user_id": 1, "username": "Marty", "credit": 0, "currency": "EUR"},
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_services",
        return_value=SERVICES_DATA,
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_gameserver",
        return_value=GAMESERVER_DATA,
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_games_catalog",
        return_value=GAMES_CATALOG,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_game_icon_resolves_to_largest_available_size(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("image", DOMAIN, "1_game_icon")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state.attributes.get("entity_picture") is not None


async def test_game_icon_falls_back_to_smaller_size_when_missing(hass):
    # Minecraft (Technic) entry in the fixture only has x256/x120, no x64/x32/x16.
    # Add a service using that folder_short to confirm the preference order works.
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "test-token"},
        options={CONF_SERVICES: [4]},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_user",
        return_value={"user_id": 1, "username": "Marty", "credit": 0, "currency": "EUR"},
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_services",
        return_value=[
            {
                "id": 4,
                "status": "active",
                "auto_extension": True,
                "details": {"folder_short": "minecrafttekkit"},
            }
        ],
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_gameserver",
        return_value=GAMESERVER_DATA,
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_games_catalog",
        return_value=GAMES_CATALOG,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("image", DOMAIN, "4_game_icon")
    assert hass.states.get(entity_id).attributes.get("entity_picture") is not None


async def test_no_game_icon_entity_when_folder_short_not_in_catalog(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    # Service 2 has a folder_short that doesn't exist in the catalog fixture
    # -> no resolvable icon -> the entity is never created (ImageEntity
    # always exposes an entity_picture proxy URL regardless of whether the
    # underlying image_url is set, so "created but empty" isn't a usable
    # signal here).
    assert registry.async_get_entity_id("image", DOMAIN, "2_game_icon") is None


async def test_no_game_icon_entity_when_catalog_entry_has_no_icons(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    assert registry.async_get_entity_id("image", DOMAIN, "3_game_icon") is None
