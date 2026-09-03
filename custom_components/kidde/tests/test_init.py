"""Tests for the Kidde HomeSafe integration."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from kidde_homesafe import KiddeClient, KiddeDataset
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kidde import (
    async_remove_config_entry_device,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.kidde.const import DOMAIN
from custom_components.kidde.coordinator import KiddeCoordinator


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
        assert await async_setup_entry(hass, entry) is True
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
        await async_setup_entry(hass, entry)
        assert await async_unload_entry(hass, entry) is True
        assert entry.state == ConfigEntryState.NOT_LOADED


def _add_coordinator(
    hass: HomeAssistant, entry: MockConfigEntry, data: KiddeDataset | None
) -> KiddeCoordinator:
    """Register a coordinator holding ``data`` for ``entry`` in hass.data."""
    coordinator = KiddeCoordinator(
        hass, KiddeClient("mock_cookie"), update_interval=60
    )
    coordinator.data = data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    return coordinator


def _mock_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create and register a config entry for removal tests."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"cookies": "mock_cookie", "update_interval": 60},
        unique_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.asyncio
async def test_remove_device_refused_while_kidde_reports_it(
    hass: HomeAssistant,
) -> None:
    """Removal is refused for a device Kidde still reports."""
    entry = _mock_entry(hass)
    _add_coordinator(
        hass,
        entry,
        KiddeDataset(
            locations={},
            devices={12345: {"label": "Front Door", "id": 12345}},
            events=None,
        ),
    )

    # entity.py registers devices by label, while KiddeDataset.devices is
    # keyed by integer id -- the label is what must be matched.
    device = DeviceEntry(identifiers={(DOMAIN, "Front Door")})

    assert await async_remove_config_entry_device(hass, entry, device) is False


@pytest.mark.asyncio
async def test_remove_device_allowed_when_kidde_no_longer_reports_it(
    hass: HomeAssistant,
) -> None:
    """Removal is allowed for a stale device Kidde no longer reports."""
    entry = _mock_entry(hass)
    _add_coordinator(
        hass,
        entry,
        KiddeDataset(
            locations={},
            devices={12345: {"label": "Front Door", "id": 12345}},
            events=None,
        ),
    )

    device = DeviceEntry(identifiers={(DOMAIN, "Removed Detector")})

    assert await async_remove_config_entry_device(hass, entry, device) is True


@pytest.mark.asyncio
async def test_remove_device_ignores_identifiers_from_other_domains(
    hass: HomeAssistant,
) -> None:
    """A matching label under a different domain does not block removal."""
    entry = _mock_entry(hass)
    _add_coordinator(
        hass,
        entry,
        KiddeDataset(
            locations={},
            devices={12345: {"label": "Front Door", "id": 12345}},
            events=None,
        ),
    )

    device = DeviceEntry(identifiers={("other_domain", "Front Door")})

    assert await async_remove_config_entry_device(hass, entry, device) is True


@pytest.mark.asyncio
async def test_remove_device_allowed_when_entry_not_loaded(
    hass: HomeAssistant,
) -> None:
    """Removal fails open when the entry has no coordinator in hass.data."""
    entry = _mock_entry(hass)

    device = DeviceEntry(identifiers={(DOMAIN, "Front Door")})

    # No coordinator registered at all: unloaded or failed setup.
    assert await async_remove_config_entry_device(hass, entry, device) is True


@pytest.mark.asyncio
async def test_remove_device_allowed_when_coordinator_data_is_none(
    hass: HomeAssistant,
) -> None:
    """Removal fails open when the initial refresh never populated data."""
    entry = _mock_entry(hass)
    _add_coordinator(hass, entry, None)

    device = DeviceEntry(identifiers={(DOMAIN, "Front Door")})

    assert await async_remove_config_entry_device(hass, entry, device) is True


@pytest.mark.asyncio
async def test_remove_device_allowed_when_devices_not_fetched(
    hass: HomeAssistant,
) -> None:
    """Removal fails open when the dataset carries no devices."""
    entry = _mock_entry(hass)
    _add_coordinator(
        hass, entry, KiddeDataset(locations={}, devices=None, events=None)
    )

    device = DeviceEntry(identifiers={(DOMAIN, "Front Door")})

    assert await async_remove_config_entry_device(hass, entry, device) is True
