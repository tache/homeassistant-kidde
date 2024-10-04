"""The Kidde HomeSafe integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from kidde_homesafe import KiddeClient

from .const import DOMAIN
from .coordinator import KiddeCoordinator

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kidde HomeSafe from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    client = KiddeClient(entry.data["cookies"])
    hass.data[DOMAIN][entry.entry_id] = coordinator = KiddeCoordinator(
        hass, client, update_interval=entry.data["update_interval"]
    )
    await coordinator.async_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> bool:
    """Remove a Kidde device associated with a config entry."""

    for identifier in device.identifiers:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Removing Device: [%s]",
                identifier,
            )
            logger.debug(
                "Entry ID: [%s]",
                entry.entry_id,
            )
            logger.debug(
                "Device ID: [%s]",
                device.id,
            )
            logger.debug(
                "Identifier in Devices: [%r]",
                identifier[1] in hass.data[DOMAIN][entry.entry_id].data.devices,
            )
            for devi in hass.data[DOMAIN][entry.entry_id].data.devices:
                logger.debug("Devices: [%s] [%s]", devi.entry_id)

        if (
            identifier[0] == DOMAIN
            and identifier[1] in hass.data[DOMAIN][entry.entry_id].data.devices
        ):
            return False

    return True
