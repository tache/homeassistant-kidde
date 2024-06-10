"""Sensor platform for Kidde Homesafe integration."""

from __future__ import annotations
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.number import NumberDeviceClass
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

_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        "smoke_level",
        icon="mdi:smoke",
        name="Smoke Level",
        device_class=SensorDeviceClass.AQI,
    ),
    SensorEntityDescription(
        "co_level",
        icon="mdi:molecule-co",
        name="CO Level",
        device_class=SensorDeviceClass.CO,
    ),
    SensorEntityDescription(
        "battery_state",
        icon="mdi:battery-alert",
        name="Battery State",
        device_class=SensorDeviceClass.ENUM,
        options=["ok", "failed"],
    ),
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
    SensorEntityDescription(
        "overall_iaq_status",
        icon="mdi:air-filter",
        name="Overall Air Quality",
        device_class=SensorDeviceClass.AQI,
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


class KiddeSensorEntity(KiddeEntity, SensorEntity):
    """Sensor for Kidde HomeSafe."""

    @property
    def native_value(self) -> str:
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
