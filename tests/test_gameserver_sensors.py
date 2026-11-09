"""Tests for the gameserver-derived sensors (players, map, version, memory, ...)."""
from unittest.mock import patch

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nitrado.const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN

# Trimmed example /services/{id}/gameservers payload as documented by
# Nitrado, for a Minecraft server that DOES answer the query protocol.
MINECRAFT_GAMESERVER = {
    "must_be_started": True,
    "status": "started",
    "game": "mc",
    "game_human": "Minecraft Vanilla",
    "memory_mb": 1024,
    "query": {
        "server_name": "Minecraft Server",
        "connect_ip": "127.0.0.1:25565",
        "map": "random",
        "version": "1.8",
        "player_current": 1,
        "player_max": 4,
        "players": [{"id": 1, "name": "Tyrola", "score": 0, "ping": 8}],
    },
}

# A game that does NOT answer the query protocol: no "query" key at all.
NO_QUERY_GAMESERVER = {
    "must_be_started": True,
    "status": "started",
    "game": "csgo",
    "game_human": "Counter-Strike",
    "memory_mb": 2048,
}

SERVICES_DATA = [
    {"id": 1, "status": "active", "auto_extension": True, "type_human": "Gameserver 4 Slots"},
    {"id": 2, "status": "active", "auto_extension": True, "type_human": "Gameserver 10 Slots"},
]


async def _setup_entry(hass, gameservers: dict[int, dict]):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "test-token"},
        options={CONF_SERVICES: [1, 2]},
    )
    entry.add_to_hass(hass)

    async def fake_get_gameserver(self, service_id):
        return gameservers[service_id]

    with patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_user",
        return_value={"user_id": 1, "username": "Marty", "credit": 0, "currency": "EUR"},
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_services",
        return_value=SERVICES_DATA,
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_gameserver",
        fake_get_gameserver,
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_games_catalog",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_player_count_sensor_with_query_support(hass):
    await _setup_entry(hass, {1: MINECRAFT_GAMESERVER, 2: NO_QUERY_GAMESERVER})
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "1_player_count")
    state = hass.states.get(entity_id)

    assert state.state == "1"
    assert state.attributes["max"] == 4
    assert state.attributes["players"] == ["Tyrola"]
    assert state.attributes["unit_of_measurement"] == "players"


async def test_player_count_sensor_without_query_support_is_unknown(hass):
    await _setup_entry(hass, {1: MINECRAFT_GAMESERVER, 2: NO_QUERY_GAMESERVER})
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "2_player_count")
    state = hass.states.get(entity_id)

    assert state.state == "unknown"
    assert "max" not in state.attributes
    assert "players" not in state.attributes


async def test_game_sensor_prefers_game_human(hass):
    await _setup_entry(hass, {1: MINECRAFT_GAMESERVER, 2: NO_QUERY_GAMESERVER})
    registry = er.async_get(hass)

    assert (
        hass.states.get(registry.async_get_entity_id("sensor", DOMAIN, "1_game")).state
        == "Minecraft Vanilla"
    )
    assert (
        hass.states.get(registry.async_get_entity_id("sensor", DOMAIN, "2_game")).state
        == "Counter-Strike"
    )


async def test_map_version_and_connect_address_sensors(hass):
    await _setup_entry(hass, {1: MINECRAFT_GAMESERVER, 2: NO_QUERY_GAMESERVER})
    registry = er.async_get(hass)

    assert hass.states.get(registry.async_get_entity_id("sensor", DOMAIN, "1_map")).state == "random"
    assert hass.states.get(registry.async_get_entity_id("sensor", DOMAIN, "1_version")).state == "1.8"
    assert (
        hass.states.get(registry.async_get_entity_id("sensor", DOMAIN, "1_connect_address")).state
        == "127.0.0.1:25565"
    )
    # No query data for service 2 -> sensors exist but stay unknown.
    assert hass.states.get(registry.async_get_entity_id("sensor", DOMAIN, "2_map")).state == "unknown"


async def test_must_be_started_binary_sensor(hass):
    await _setup_entry(hass, {1: MINECRAFT_GAMESERVER, 2: NO_QUERY_GAMESERVER})
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("binary_sensor", DOMAIN, "1_must_be_started")
    assert hass.states.get(entity_id).state == "on"


async def test_memory_sensor_only_for_minecraft_and_hytale(hass):
    await _setup_entry(hass, {1: MINECRAFT_GAMESERVER, 2: NO_QUERY_GAMESERVER})
    registry = er.async_get(hass)

    # Minecraft -> memory sensor exists.
    minecraft_entity = registry.async_get_entity_id("sensor", DOMAIN, "1_memory")
    assert minecraft_entity is not None
    assert hass.states.get(minecraft_entity).state == "1024"
    assert hass.states.get(minecraft_entity).attributes["unit_of_measurement"] == "MB"

    # Counter-Strike -> no memory sensor at all.
    assert registry.async_get_entity_id("sensor", DOMAIN, "2_memory") is None
