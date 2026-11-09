"""Tests for the re-authentication flow."""
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState, SOURCE_REAUTH
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nitrado.api import NitradoAuthError
from custom_components.nitrado.const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN

API = "custom_components.nitrado.api.NitradoApiClient"


def _entry(hass) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "old-token"},
        options={CONF_SERVICES: [1]},
    )
    entry.add_to_hass(hass)
    return entry


async def test_rejected_token_starts_reauth(hass):
    entry = _entry(hass)

    with patch(f"{API}.async_get_services", side_effect=NitradoAuthError("nope")), patch(
        f"{API}.async_get_user", return_value={}
    ), patch(f"{API}.async_get_games_catalog", return_value=[]):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert flows[0]["step_id"] == "reauth_confirm"


async def test_reauth_flow_updates_token(hass):
    entry = _entry(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(f"{API}.async_get_services", return_value=[]), patch(
        "custom_components.nitrado.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "new-token"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_API_TOKEN] == "new-token"
    assert entry.options[CONF_SERVICES] == [1]


async def test_reauth_flow_invalid_token_shows_error(hass):
    entry = _entry(hass)
    result = await entry.start_reauth_flow(hass)

    with patch(f"{API}.async_get_services", side_effect=NitradoAuthError("nope")):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "still-bad"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
    assert entry.data[CONF_API_TOKEN] == "old-token"
