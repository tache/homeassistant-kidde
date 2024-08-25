"""Button platform for Kidde Homesafe integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KiddeCoordinator
from .entity import KiddeCommand
from .entity import KiddeEntity

# Constants for dictionary keys
KEY_MODEL = "model"

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
        if coordinator.data.devices[device_id].get(KEY_MODEL, None) == "wifiiaqdetector":
            for entity_description in _BUTTON_DESCRIPTIONS:
                sensors.append(
                    KiddeButtonEntity(coordinator, device_id, entity_description)
                )
        elif coordinator.data.devices[device_id].get(KEY_MODEL, None) == "waterleakdetector":
            pass # TODO: fill this later
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.warning(
                    "Unexpected model [%s]",
                    coordinator.data.devices[device_id].get(KEY_MODEL, None),
                )

    async_add_devices(sensors)


class KiddeButtonEntity(KiddeEntity, ButtonEntity):
    """Button for Kidde HomeSafe."""

    entity_description: KiddeButtonEntityDescription

    async def async_press(self) -> None:
        """Press the entity."""
        await self.kidde_command(self.entity_description.kidde_command)
