"""Button platform for Kidde Homesafe integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KiddeCoordinator
from .entity import KiddeCommand, KiddeEntity

# Constants for dictionary keys
KEY_MODEL = "model"

logger = logging.getLogger(__name__)


@dataclass
class KiddeButtonEntityDescriptionMixin:
    """Mixin for required keys."""

    kidde_command: KiddeCommand


@dataclass
class KiddeButtonEntityDescription(
    ButtonEntityDescription, KiddeButtonEntityDescriptionMixin
):
    """Describes Kidde Button entity."""


_BUTTON_DESCRIPTIONS = (
    KiddeButtonEntityDescription(
        key="test",
        icon="mdi:smoke-detector-variant-alert",
        name="Test",
        kidde_command=KiddeCommand.TEST,
    ),
    KiddeButtonEntityDescription(
        key="hush",
        icon="mdi:smoke-detector-variant-off",
        name="Hush",
        kidde_command=KiddeCommand.HUSH,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback) -> None:
    """Set up the button platform."""
    coordinator: KiddeCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    for device_id in coordinator.data.devices:
        match coordinator.data.devices[device_id].get(KEY_MODEL, None):
            case "wifiiaqdetector" | "wifidetector":
                for entity_description in _BUTTON_DESCRIPTIONS:
                    sensors.append(
                        KiddeButtonEntity(coordinator, device_id, entity_description)
                    )

            case "waterleakdetector" | "cowifidetector":
                pass  # TODO: Buttons for the other devices?

            case _:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.warning(
                        "Unverified Kidde Device Model: [%s]",
                        coordinator.data.devices[device_id].get(KEY_MODEL, None),
                    )

    async_add_devices(sensors)


class KiddeButtonEntity(KiddeEntity, ButtonEntity):
    """Button for Kidde HomeSafe."""

    entity_description: KiddeButtonEntityDescription

    async def async_press(self) -> None:
        """Press the entity."""
        await self.kidde_command(self.entity_description.kidde_command)
