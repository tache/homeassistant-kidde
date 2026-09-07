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

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kidde HomeSafe from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    client = KiddeClient(entry.data["cookies"])
    # The interval chosen at setup is stored in data; later edits from the
    # options flow are stored in options, which therefore wins.
    update_interval = entry.options.get(
        "update_interval", entry.data["update_interval"]
    )
    hass.data[DOMAIN][entry.entry_id] = coordinator = KiddeCoordinator(
        hass, client, update_interval=update_interval
    )
    await coordinator.async_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry so a changed update interval takes effect."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> bool:
    """Authorize removal of a device that Kidde no longer reports.

    Home Assistant calls this to decide whether the user is allowed to delete
    ``device`` from the device registry; it does not perform the removal.

    Removal is refused while Kidde still reports the device, because every
    platform rebuilds its entities from the coordinator data on the next
    reload and the device would immediately reappear. Devices missing from
    the coordinator data are stale and may be removed. Removal also defaults
    to allowed when that data cannot be read at all -- the entry is unloaded
    or failed, or the initial refresh never succeeded -- so that a broken
    entry does not trap orphaned devices in the registry.
    """
    entries: dict = hass.data.get(DOMAIN, {})
    coordinator: KiddeCoordinator | None = entries.get(entry.entry_id)
    dataset = coordinator.data if coordinator is not None else None
    devices = dataset.devices if dataset is not None else None

    # KiddeDataset.devices is keyed by integer device id, so match on the
    # label instead: that is what entity.py registers as the identifier.
    known_labels = {
        device_data.get("label") for device_data in (devices or {}).values()
    }
    _LOGGER.debug("Known Kidde device labels: %s", known_labels)

    return not any(
        domain == DOMAIN and identifier in known_labels
        for domain, identifier in device.identifiers
    )
