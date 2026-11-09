"""Integration tests for the Nitrado account device (sensors + avatar)."""
from unittest.mock import patch

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nitrado.const import CONF_API_TOKEN, CONF_SERVICES, DOMAIN

# Full example /user payload as documented by Nitrado, including the fields
# (email, profile/address) the integration must NOT turn into entities.
USER_DATA = {
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
    "two_factor": ["u2f", "google"],
    "profile": {
        "name": "Marty McFly",
        "street": "DeLorean Street 12",
        "postcode": "2209",
        "city": "Hill Valley",
        "country": "US",
        "state": "CA",
        "country_and_state_verified": True,
        "newsletter": True,
    },
    "permissions": ["TWITCH_WHITELISTING"],
    "employee": False,
    "partner_id": 139,
    "can_update_username": False,
    "newsletter_campaigns": [
        {
            "id": 1,
            "offer_page_id": 467,
            "loca_key": "nlc_squad",
            "name": "Newsletter Campaign für Squad",
            "game_name": "squad",
        }
    ],
    "allowed_to_spend_credits": True,
    "has_rootserver": False,
}


async def _setup_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "test-token"},
        options={CONF_SERVICES: []},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_user",
        return_value=USER_DATA,
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_services",
        return_value=[],
    ), patch(
        "custom_components.nitrado.api.NitradoApiClient.async_get_games_catalog",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_credit_sensor_converts_cents_to_currency(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "1337_credit")
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert float(state.state) == 19.55
    assert state.attributes["unit_of_measurement"] == "EUR"
    assert state.attributes["device_class"] == "monetary"


async def test_user_id_and_username_sensors(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    user_id_entity = registry.async_get_entity_id("sensor", DOMAIN, "1337_user_id")
    username_entity = registry.async_get_entity_id("sensor", DOMAIN, "1337_username")
    assert user_id_entity is not None
    assert username_entity is not None

    assert hass.states.get(user_id_entity).state == "1337"
    assert hass.states.get(username_entity).state == "Marty"

    # Both are identification info, not primary metrics -> diagnostic category.
    assert registry.async_get(user_id_entity).entity_category == EntityCategory.DIAGNOSTIC
    assert registry.async_get(username_entity).entity_category == EntityCategory.DIAGNOSTIC


async def test_avatar_image_entity_is_created(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id("image", DOMAIN, "1337_avatar")
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes.get("entity_picture") is not None


async def test_account_device_groups_all_entities(hass):
    await _setup_entry(hass)
    registry = er.async_get(hass)

    device_ids = {
        registry.async_get(registry.async_get_entity_id("sensor", DOMAIN, "1337_credit")).device_id,
        registry.async_get(registry.async_get_entity_id("sensor", DOMAIN, "1337_user_id")).device_id,
        registry.async_get(registry.async_get_entity_id("sensor", DOMAIN, "1337_username")).device_id,
        registry.async_get(registry.async_get_entity_id("image", DOMAIN, "1337_avatar")).device_id,
    }
    assert len(device_ids) == 1
    assert None not in device_ids


async def test_email_and_address_are_never_exposed(hass):
    """Email and postal address from the API must not leak into any entity."""
    await _setup_entry(hass)

    for state in hass.states.async_all():
        blob = repr(state.attributes) + state.state
        assert "marty.mcfly@biffco.com" not in blob
        assert "DeLorean Street" not in blob
        assert "Hill Valley" not in blob
