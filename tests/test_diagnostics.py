"""Tests for the Nitrado diagnostics redaction."""
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nitrado.const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN
from custom_components.nitrado.diagnostics import async_get_config_entry_diagnostics

USER_DATA = {
    "user_id": 1337,
    "username": "Marty",
    "email": "marty.mcfly@biffco.com",
    "credit": 1955,
    "currency": "EUR",
    "profile": {
        "name": "Marty McFly",
        "street": "DeLorean Street 12",
        "city": "Hill Valley",
    },
}

SERVICES_DATA = [
    {"id": 1, "user_id": 1337, "status": "active", "auto_extension": True}
]

GAMESERVER_DATA = {
    "status": "started",
    "username": "ni1234_1",
    "user_id": 1337,
    "websocket_token": "super-secret-token",
    "credentials": {
        "ftp": {"username": "ni1_1", "password": "hunter2"},
        "mysql": {"username": "ni1_1", "password": "hunter2"},
    },
}


async def test_diagnostics_redacts_sensitive_fields(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "test-token"},
        options={CONF_SERVICES: [1]},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_user",
        return_value=USER_DATA,
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

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    blob = repr(diagnostics)

    assert diagnostics["entry_data"][CONF_API_TOKEN] == "**REDACTED**"
    assert diagnostics["account"]["email"] == "**REDACTED**"
    assert diagnostics["account"]["profile"] == "**REDACTED**"
    assert diagnostics["services"][1]["gameserver"]["websocket_token"] == "**REDACTED**"
    assert diagnostics["services"][1]["gameserver"]["credentials"] == "**REDACTED**"

    # Belt and suspenders: none of the raw secrets appear anywhere in the dump.
    assert "test-token" not in blob
    assert "marty.mcfly@biffco.com" not in blob
    assert "DeLorean Street" not in blob
    assert "super-secret-token" not in blob
    assert "hunter2" not in blob

    # Owner identifiers are redacted everywhere, including the services section.
    assert diagnostics["account"]["username"] == "**REDACTED**"
    assert diagnostics["account"]["user_id"] == "**REDACTED**"
    assert diagnostics["services"][1]["gameserver"]["username"] == "**REDACTED**"
    assert diagnostics["services"][1]["contract"]["user_id"] == "**REDACTED**"
    assert "Marty" not in blob
    assert "ni1234_1" not in blob
    assert "1337" not in blob

    # Non-sensitive data must survive untouched.
    assert diagnostics["services"][1]["gameserver"]["status"] == "started"
