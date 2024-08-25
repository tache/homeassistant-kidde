"""Binary sensor platform for Kidde Homesafe integration."""

from __future__ import annotations
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    EntityCategory,
    UnitOfTime,
)

from .const import DOMAIN
from .coordinator import KiddeCoordinator
from .entity import KiddeEntity

# Constants for dictionary keys
KEY_MODEL = "model"

logger = logging.getLogger(__name__)


_IAQ_BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="smoke_alarm",
        icon="mdi:smoke-detector-variant-alert",
        name="Smoke Alarm",
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
    BinarySensorEntityDescription(
        key="smoke_hushed",
        icon="mdi:smoke-detector-variant-off",
        name="Smoke Hushed",
    ),
    BinarySensorEntityDescription(
        key="co_alarm",
        icon="mdi:molecule-co",
        name="CO Alarm",
        device_class=BinarySensorDeviceClass.CO,
    ),
    BinarySensorEntityDescription(
        key="hardwire_smoke",
        icon="mdi:smoke-detector-variant-alert",
        name="Hardwire Smoke Alarm",
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
    BinarySensorEntityDescription(
        key="too_much_smoke",
        icon="mdi:smoke-detector-variant-alert",
        name="Too Much Smoke",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
)

_COMMON_BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="contact_lost",
        icon="mdi:smoke-detector-variant-off",
        name="Contact Lost",
    ),
    BinarySensorEntityDescription(
        key="lost",
        icon="mdi:smoke-detector-variant-off",
        name="Lost",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

_WATER_BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="water_alarm",
        icon="mdi:water-alert",
        name="Water Alert",
    ),
    BinarySensorEntityDescription(
        key="low_temp_alarm",
        icon="mdi:snowflake-alert",
        name="Freeze Alert",
    ),
    BinarySensorEntityDescription(
        key="low_battery_alarm",
        icon="mdi:battery-alert-variant",
        name="Battery Low Alert",
    ),
    BinarySensorEntityDescription(
        key="reset_flag",
        icon="mdi:history",
        name="Reset Flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

_INVERSE_BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="offline",
        icon="mdi:wifi-alert",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)

_BATTERY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="battery_state",
        icon="mdi:battery",
        name="Battery State",
        device_class=BinarySensorDeviceClass.BATTERY
    ),
)


def add_sensors(
    coordinator: KiddeCoordinator,
    device_id: str,
    descriptions: tuple[BinarySensorEntityDescription],
    sensor_class: type[BinarySensorEntity],
    sensors: list[BinarySensorEntity]
) -> None:
    """Add sensors to the sensors list based on entity descriptions and sensor class."""
    sensors.extend(
        sensor_class(coordinator, device_id, entity_description)
        for entity_description in descriptions
    )

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback) -> None:
    """Set up the binary sensor platform."""
    coordinator: KiddeCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    model_sensor_mapping = {
        "wifiiaqdetector": _IAQ_BINARY_SENSOR_DESCRIPTIONS,
        "waterleakdetector": _WATER_BINARY_SENSOR_DESCRIPTIONS,
    }

    for device_id, device_data in coordinator.data.devices.items():
        model = device_data.get(KEY_MODEL)

        if model is None:
            logger.warning("No model found for device [%s]", device_id)
            continue

        entity_descriptions = model_sensor_mapping.get(model)

        if entity_descriptions is not None:
            # Add model-specific sensors
            add_sensors(coordinator, device_id, entity_descriptions, KiddeBinarySensorEntity, sensors)
        else:
            logger.warning("Unexpected model [%s]", model)

        # Add common sensors regardless of model
        sensor_mapping = [
            (_COMMON_BINARY_SENSOR_DESCRIPTIONS, KiddeBinarySensorEntity),
            (_BATTERY_SENSOR_DESCRIPTIONS, KiddeBatteryStateSensorEntity),
            (_INVERSE_BINARY_SENSOR_DESCRIPTIONS, KiddeInverseBinarySensorEntity),
        ]

        for descriptions, sensor_class in sensor_mapping:
            add_sensors(coordinator, device_id, descriptions, sensor_class, sensors)

    async_add_devices(sensors)

class KiddeBinarySensorEntity(KiddeEntity, BinarySensorEntity):
    """Binary sensor for Kidde HomeSafe."""

    @property
    def is_on(self) -> bool | None:
        """Return the value of the binary sensor."""
        return self.kidde_device.get(self.entity_description.key)

class KiddeInverseBinarySensorEntity(KiddeEntity, BinarySensorEntity):
    """Binary sensor for Kidde HomeSafe."""

    @property
    def is_on(self) -> bool | None:
        """Return the value of the binary sensor."""
        return self.kidde_device.get(self.entity_description.key) == False

class KiddeBatteryStateSensorEntity(KiddeEntity, BinarySensorEntity):
    """Binary sensor for Kidde HomeSafe."""

    @property
    def is_on(self) -> bool | None:
        """Return the value of the binary sensor."""
        return self.kidde_device.get(self.entity_description.key) != "ok"
