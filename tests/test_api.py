"""Tests for the Nitrado API client, against a mocked /user response."""
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest

from custom_components.nitrado.api import (
    NitradoApiClient,
    NitradoAuthError,
)
from custom_components.nitrado.const import API_BASE_URL

# Example payload as documented by Nitrado for a successful /user call.
USER_RESPONSE = {
    "status": "success",
    "data": {
        "user": {
            "user_id": 1337,
            "username": "Marty",
            "activated": True,
            "timezone": "America/Los_Angeles",
            "email": "marty.mcfly@biffco.com",
            "credit": 1955,
            "currency": "EUR",
            "registered": "1985-25-10T01:15:00.000+00:00",
            "language": "eng",
            "avatar": "https://server.nitrado.net/users.nitrado/1337.jpg",
            "donations": True,
            "profile": {
                "name": "Marty McFly",
                "street": "DeLorean Street 12",
                "postcode": "2209",
                "city": "Hill Valley",
                "country": "US",
                "state": "CA",
            },
            "has_rootserver": False,
        }
    },
}


async def test_async_get_user_parses_response(hass, aioclient_mock):
    aioclient_mock.get(f"{API_BASE_URL}/user", json=USER_RESPONSE)
    client = NitradoApiClient(async_get_clientsession(hass), "test-token")

    user = await client.async_get_user()

    assert user["user_id"] == 1337
    assert user["username"] == "Marty"
    assert user["credit"] == 1955
    assert user["currency"] == "EUR"
    assert user["avatar"] == "https://server.nitrado.net/users.nitrado/1337.jpg"


async def test_async_get_user_sends_bearer_token(hass, aioclient_mock):
    aioclient_mock.get(f"{API_BASE_URL}/user", json=USER_RESPONSE)
    client = NitradoApiClient(async_get_clientsession(hass), "secret-token")

    await client.async_get_user()

    assert aioclient_mock.mock_calls[0][3]["Authorization"] == "Bearer secret-token"


async def test_async_get_user_raises_on_invalid_token(hass, aioclient_mock):
    aioclient_mock.get(f"{API_BASE_URL}/user", status=401)
    client = NitradoApiClient(async_get_clientsession(hass), "bad-token")

    with pytest.raises(NitradoAuthError):
        await client.async_get_user()
