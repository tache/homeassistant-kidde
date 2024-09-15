"""Entity base class for Kidde HomeSafe."""

from __future__ import annotations

import logging

from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from kidde_homesafe import KiddeCommand

from .const import DOMAIN, MANUFACTURER
from .coordinator import KiddeCoordinator

# Constants for dictionary keys
KEY_MODEL = "model"

logger = logging.getLogger(__name__)


class KiddeEntity(CoordinatorEntity[KiddeCoordinator]):
    """Entity base class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KiddeCoordinator,
        device_id: int,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.entity_description = entity_description

    @property
    def kidde_device(self) -> dict:
        """The device from the coordinator's data."""
        return self.coordinator.data.devices[self.device_id]

    @property
    def unique_id(self) -> str:
        """Return the unique id of the device."""
        return f"{self.kidde_device['label']}_{self.entity_description.key}"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device information of the device."""
        device = self.kidde_device

        model_type = device.get(KEY_MODEL, None)
        model_string = ""
        match model_type:
            case "wifiiaqdetector":
                model_string = f"Smoke Detector with IAQ ({model_type})"
            case "waterleakdetector":
                model_string = f"Water Leak + Freeze Detector ({model_type})"
            case "wifidetector":
                model_string = f"Smoke Detector ({model_type})"
            case "cowifidetector":
                model_string = f"Carbon Monoxide Detector ({model_type})"
            case _:
                model_string = f"{model_type}"
                if logger.isEnabledFor(logging.DEBUG):
                    logger.warning(
                        "Unverified Kidde Device Model: [%s] ... Please send Kidde device data to maintainers.",
                        model_type,
                    )

        return DeviceInfo(
            identifiers={(DOMAIN, device["label"])},
            name=device.get("label"),
            hw_version=device.get("hwrev"),
            sw_version=str(device.get("fwrev")),
            model=model_string,
            serial_number=device.get("serial_number"),
            manufacturer=MANUFACTURER,
        )

    async def kidde_command(self, command: KiddeCommand) -> None:
        """Send a Kidde command for this device."""
        client = self.coordinator.client
        device = self.kidde_device
        await client.device_command(device["location_id"], device["id"], command)
