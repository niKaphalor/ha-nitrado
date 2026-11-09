"""Tests for the per-service contract sensors (status, expiry, auto-extension)."""
from unittest.mock import patch

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nitrado.const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN

# Trimmed example /services payload as documented by Nitrado.
SERVICES_DATA = [
    {
        "id": 3,
        "status": "active",
        "comment": "This is my special Battlefield Server.",
        "auto_extension": False,
        "type_human": "Gameserver 16 Slots",
        "details": {
            "address": "10.10.0.6:27015",
            "name": "Nitrado.net Battlefield 4 Server",
            "game": "Battlefield 4",
            "slots": 16,
            "game_slots": 16,
        },
        "suspend_date": "2017-02-09T22:26:46",
        "delete_date": "2017-02-19T22:26:46",
    },
    {
        "id": 6,
        "status": "active",
        "comment": None,
        "auto_extension": True,
        "type_human": "Gameserver 4 Slots",
        "details": {
            "address": "10.10.0.7:27015",
            "name": "Nitrado.net Minecraft Server",
            "game": "Minecraft",
            "slots": 4,
            "game_slots": 4,
        },
        "suspend_date": "2017-02-09T22:26:46",
        "delete_date": "2017-02-19T22:26:46",
    },
]

GAMESERVER_DATA = {"status": "started", "query": {"server_name": "Test Server"}}


async def _setup_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "test-token"},
        options={CONF_SERVICES: [3, 6]},
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
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_contract_status_sensor_and_attributes(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "3_contract_status")
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert state.state == "active"
    assert state.attributes["slots"] == 16
    assert state.attributes["address"] == "10.10.0.6:27015"
    assert state.attributes["comment"] == "This is my special Battlefield Server."
    assert state.attributes["delete_date"] == "2017-02-19T22:26:46"


async def test_expiry_date_sensor(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "3_expiry_date")
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert state.state.startswith("2017-02-09T22:26:46")


async def test_auto_extension_binary_sensor_reflects_each_service(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    off_entity = registry.async_get_entity_id("binary_sensor", DOMAIN, "3_auto_extension")
    on_entity = registry.async_get_entity_id("binary_sensor", DOMAIN, "6_auto_extension")

    assert hass.states.get(off_entity).state == "off"
    assert hass.states.get(on_entity).state == "on"


async def test_game_sensor_falls_back_to_contract_details_game(hass):
    # GAMESERVER_DATA has no game_human -> falls back to contract.details.game.
    await _setup_entry(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "3_game")
    assert entity_id is not None
    assert hass.states.get(entity_id).state == "Battlefield 4"


async def test_service_device_model_uses_type_human(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "3_status")
    device = device_registry.async_get(registry.async_get(entity_id).device_id)

    assert device.model == "Gameserver 16 Slots"
