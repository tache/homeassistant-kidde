"""Tests for the Kidde HomeSafe config flow."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from kidde_homesafe import KiddeClientAuthError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kidde.const import DOMAIN


@pytest.mark.asyncio
async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test successful user flow."""
    mock_client = MagicMock()
    mock_client.cookies = "test_cookies"

    with patch(
        "custom_components.kidde.config_flow.KiddeClient.from_login",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "email": "test@example.com",
                "password": "test_password",
                "update_interval_seconds": 30,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Kidde (test@example.com)"
        assert result["data"]["cookies"] == "test_cookies"
        assert result["data"]["update_interval"] == 30


@pytest.mark.asyncio
async def test_user_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Test user flow with invalid authentication."""
    with patch(
        "custom_components.kidde.config_flow.KiddeClient.from_login",
        side_effect=KiddeClientAuthError("Invalid credentials"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "email": "test@example.com",
                "password": "wrong_password",
                "update_interval_seconds": 30,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_reauth_flow_success(hass: HomeAssistant) -> None:
    """Test successful reauth flow."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"cookies": "old_cookies", "update_interval": 60},
        unique_id="test_entry_id",
        title="Kidde (test@example.com)",
    )
    entry.add_to_hass(hass)

    # Mock the client login
    mock_client = MagicMock()
    mock_client.cookies = "new_cookies"

    with patch(
        "custom_components.kidde.config_flow.KiddeClient.from_login",
        return_value=mock_client,
    ):
        # Initiate reauth flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        # Complete reauth with new credentials
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "email": "test@example.com",
                "password": "new_password",
            },
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"

        # Verify the entry was updated with new cookies
        assert entry.data["cookies"] == "new_cookies"
        assert entry.data["update_interval"] == 60  # Should preserve original


@pytest.mark.asyncio
async def test_reauth_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Test reauth flow with invalid authentication."""
    # Create an existing config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"cookies": "old_cookies", "update_interval": 60},
        unique_id="test_entry_id",
        title="Kidde (test@example.com)",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.kidde.config_flow.KiddeClient.from_login",
        side_effect=KiddeClientAuthError("Invalid credentials"),
    ):
        # Initiate reauth flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

        # Try to complete reauth with wrong credentials
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "email": "test@example.com",
                "password": "wrong_password",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_auth"

        # Verify the entry was NOT updated
        assert entry.data["cookies"] == "old_cookies"
