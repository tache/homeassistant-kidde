"""Binary sensor platform for Kidde Homesafe integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KiddeCoordinator
from .entity import KiddeEntity


_BINARY_SENSOR_DESCRIPTIONS = (
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
        device_class=BinarySensorDeviceClass.SMOKE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="contact_lost",
        icon="mdi:smoke-detector-variant-off",
        name="Contact_Lost",
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
        icon="mdi:battery-alert",
        name="Battery State",
        device_class=BinarySensorDeviceClass.BATTERY
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Set up the binary sensor platform."""
    coordinator: KiddeCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    for device_id in coordinator.data.devices:
        for entity_description in _BINARY_SENSOR_DESCRIPTIONS:
            sensors.append(
                KiddeBinarySensorEntity(coordinator, device_id, entity_description)
            )
        for entity_description in _INVERSE_BINARY_SENSOR_DESCRIPTIONS:
            sensors.append(
                KiddeInverseBinarySensorEntity(coordinator, device_id, entity_description)
            )
        for entity_description in _BATTERY_SENSOR_DESCRIPTIONS:
            sensors.append(
                KiddeBatteryStateSensorEntity(coordinator, device_id, entity_description)
            )
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
