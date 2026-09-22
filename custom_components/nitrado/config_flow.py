"""Config flow for the Nitrado integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api import NitradoApiClient, NitradoApiError, NitradoAuthError
from .const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _service_options(services: list[dict[str, Any]]) -> list[SelectOptionDict]:
    """Turn Nitrado services into options for the form selector."""
    return [
        SelectOptionDict(
            value=str(service["id"]),
            label=f"{service['details']['name']} ({service['details']['game']})",
        )
        for service in services
    ]


class NitradoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup: token first, then pick which servers to add."""

    VERSION = 1

    _api_token: str | None = None
    _services: list[dict[str, Any]]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = NitradoApiClient(session, user_input[CONF_API_TOKEN])
            try:
                self._services = await client.async_get_services()
            except NitradoAuthError:
                errors["base"] = "invalid_auth"
            except NitradoApiError:
                errors["base"] = "cannot_connect"
            else:
                self._api_token = user_input[CONF_API_TOKEN]
                return await self.async_step_services()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )

    async def async_step_services(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(f"nitrado_{self._api_token[:8]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Nitrado",
                data={CONF_API_TOKEN: self._api_token},
                options={CONF_SERVICES: user_input[CONF_SERVICES]},
            )

        return self.async_show_form(
            step_id="services",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERVICES): SelectSelector(
                        SelectSelectorConfig(options=_service_options(self._services), multiple=True)
                    )
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> NitradoOptionsFlow:
        return NitradoOptionsFlow(config_entry)


class NitradoOptionsFlow(config_entries.OptionsFlow):
    """Lets the user change which servers are visible after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        session = async_get_clientsession(self.hass)
        client = NitradoApiClient(session, self._config_entry.data[CONF_API_TOKEN])
        try:
            services = await client.async_get_services()
        except NitradoApiError:
            return self.async_abort(reason="cannot_connect")

        current = self._config_entry.options.get(CONF_SERVICES, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERVICES, default=current): SelectSelector(
                        SelectSelectorConfig(options=_service_options(services), multiple=True)
                    )
                }
            ),
        )
