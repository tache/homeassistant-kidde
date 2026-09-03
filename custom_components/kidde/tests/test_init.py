"""Tests for the Kidde HomeSafe integration."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kidde.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant) -> None:
    """Test the setup of a config entry."""
    # Mock a config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"cookies": "mock_cookie", "update_interval": 60},
        unique_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    # Patch coordinator and client to prevent real API calls
    with patch(
        "custom_components.kidde.coordinator.KiddeCoordinator.async_refresh",
        return_value=AsyncMock(),
    ) as mock_refresh:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state == ConfigEntryState.LOADED
        assert mock_refresh.call_count == 1


@pytest.mark.asyncio
async def test_async_unload_entry(hass: HomeAssistant) -> None:
    """Test the unloading of a config entry."""
    # Mock a config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"cookies": "mock_cookie", "update_interval": 60},
        unique_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    # Mock setup and unload functions
    with patch("custom_components.kidde.PLATFORMS", ["sensor", "switch"]):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state == ConfigEntryState.NOT_LOADED
