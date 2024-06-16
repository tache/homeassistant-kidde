"""Sensor platform for Kidde Homesafe integration."""

from __future__ import annotations
import logging
import datetime

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    UnitOfPressure,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    UnitOfTime,
)

from .const import DOMAIN
from .coordinator import KiddeCoordinator
from .entity import KiddeEntity


logger = logging.getLogger(__name__)


_TIMESTAMP_DESCRIPTIONS = (
    SensorEntityDescription(
        "last_seen",
        icon="mdi:home-clock",
        name="Last Seen",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        "last_test_time",
        icon="mdi:home-clock",
        name="Last Test Time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)

_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        "smoke_level",
        icon="mdi:smoke",
        name="Smoke Level",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.AQI,
    ),
    SensorEntityDescription(
        "co_level",
        icon="mdi:molecule-co",
        name="CO Level",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CO,
    ),
    SensorEntityDescription(
        "battery_state",
        icon="mdi:battery-alert",
        name="Battery State",
        device_class=SensorDeviceClass.ENUM,
        state_class=SensorStateClass.MEASUREMENT,
        options=["ok", "failed"],
    ),
    SensorEntityDescription(
        "life",
        icon="mdi:calendar-clock",
        name="Weeks to replace",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.WEEKS,
    ),
)

_MEASUREMENTSENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        "overall_iaq_status",
        icon="mdi:air-filter",
        name="Overall Air Quality",
        device_class=SensorDeviceClass.AQI,
    ),
    SensorEntityDescription(
        "iaq_temperature",
        name="Indoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        "humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    SensorEntityDescription(
        "hpa",
        name="Air Pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
    ),
    SensorEntityDescription(
        "tvoc",
        name="Total VOC",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
    ),
    SensorEntityDescription(
        "iaq",
        name="Indoor Air Quality",
        device_class=SensorDeviceClass.AQI,
    ),
    SensorEntityDescription(
        "co2",
        name="CO₂ Level",
        device_class=SensorDeviceClass.CO2,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: KiddeCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    for device_id in coordinator.data.devices:
        for entity_description in _TIMESTAMP_DESCRIPTIONS:
            sensors.append(
                KiddeSensorTimestampEntity(coordinator, device_id, entity_description)
            )
        for entity_description in _SENSOR_DESCRIPTIONS:
            sensors.append(
                KiddeSensorEntity(coordinator, device_id, entity_description)
            )
        if "temperature" in coordinator.data.devices[device_id].get(
            "capabilities"
        ) and coordinator.data.devices[device_id].get("iaq"):
            # The unit also has an Indoor Air Quality Monitor
            for measuremententity_description in _MEASUREMENTSENSOR_DESCRIPTIONS:
                sensors.append(
                    KiddeSensorMeasurementEntity(
                        coordinator, device_id, measuremententity_description
                    )
                )
    async_add_devices(sensors)


class KiddeSensorTimestampEntity(KiddeEntity, SensorEntity):
    """A KiddeSensoryEntity which returns a datetime.

    Assume sensor returns datetime string e.g. '2024-06-14T03:40:39.667544824Z'
    which needs to be converted to a python datetime.
    """

    @property
    def native_value(self) -> datetime.datetime | None:
        """Return the native value of the sensor."""
        value = self.kidde_device.get(self.entity_description.key)
        dtype = type(value)
        logger.debug(f"{self.entity_description.key} of type {dtype} is {value}")
        if value is None:
            return value
        return datetime.datetime.strptime(value[:-4], "%Y-%m-%dT%H:%M:%S.%f").replace(
            tzinfo=datetime.timezone.utc
        )


class KiddeSensorEntity(KiddeEntity, SensorEntity):
    """Sensor for Kidde HomeSafe."""

    @property
    def native_value(self) -> str | None | float | int:
        """Return the native value of the sensor."""
        value = self.kidde_device.get(self.entity_description.key)
        dtype = type(value)
        logger.debug(f"{self.entity_description.key} of type {dtype} is {value}")
        return value


class KiddeSensorMeasurementEntity(KiddeEntity, SensorEntity):
    """Measurement Sensor for Kidde HomeSafe."""

    @property
    def state_class(self) -> str:
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        """Return the native value of the sensor."""
        return self.kidde_device.get(self.entity_description.key).get("value")

    @property
    def native_unit_of_measurement(self) -> string:
        """Return the native unit of measurement of the sensor."""
        match self.kidde_device.get(self.entity_description.key).get("Unit").upper():
            case "C":
                return UnitOfTemperature.CELSIUS
            case "F":
                return UnitOfTemperature.FAHRENHEIT
            case "%RH":
                return PERCENTAGE
            case "HPA":
                return UnitOfPressure.HPA
            case "PPB":
                return CONCENTRATION_PARTS_PER_BILLION
            case "PPM":
                return CONCENTRATION_PARTS_PER_MILLION
            case _:
                return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes for the value sensor (Status)."""
        return {
            "Status": self.kidde_device.get(self.entity_description.key).get("status")
        }
