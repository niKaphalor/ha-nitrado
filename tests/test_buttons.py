"""Tests for the start/stop/restart buttons."""
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nitrado.api import NitradoApiError
from custom_components.nitrado.const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN

SERVICES_DATA = [{"id": 1, "status": "active", "auto_extension": True}]
GAMESERVER_DATA = {"status": "started"}


@contextmanager
def _patched_reads():
    """Mock the read endpoints for the whole test, including refreshes triggered by button presses."""
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
        yield


async def _setup_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "test-token"},
        options={CONF_SERVICES: [1]},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_start_and_restart_buttons_call_the_restart_endpoint(hass):
    with _patched_reads():
        await _setup_entry(hass)
        registry = er.async_get(hass)

        with patch(
            "custom_components.nitrado.api.NitradoApiClient.async_restart_gameserver",
            new_callable=AsyncMock,
        ) as mock_restart:
            for unique_id in ("1_start", "1_restart"):
                entity_id = registry.async_get_entity_id("button", DOMAIN, unique_id)
                assert entity_id is not None
                await hass.services.async_call(
                    "button", "press", {"entity_id": entity_id}, blocking=True
                )

        assert mock_restart.call_count == 2
        mock_restart.assert_called_with(1)


async def test_stop_button_calls_the_stop_endpoint(hass):
    with _patched_reads():
        await _setup_entry(hass)
        registry = er.async_get(hass)

        with patch(
            "custom_components.nitrado.api.NitradoApiClient.async_stop_gameserver",
            new_callable=AsyncMock,
        ) as mock_stop:
            entity_id = registry.async_get_entity_id("button", DOMAIN, "1_stop")
            await hass.services.async_call(
                "button", "press", {"entity_id": entity_id}, blocking=True
            )

        mock_stop.assert_called_once_with(1)


async def test_button_press_surfaces_api_errors(hass):
    with _patched_reads():
        await _setup_entry(hass)
        registry = er.async_get(hass)

        with patch(
            "custom_components.nitrado.api.NitradoApiClient.async_stop_gameserver",
            side_effect=NitradoApiError("403 forbidden"),
        ):
            entity_id = registry.async_get_entity_id("button", DOMAIN, "1_stop")
            with pytest.raises(HomeAssistantError):
                await hass.services.async_call(
                    "button", "press", {"entity_id": entity_id}, blocking=True
                )
