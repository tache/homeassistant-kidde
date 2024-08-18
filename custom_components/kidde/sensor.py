"""Sensor platform for Kidde Homesafe integration."""

from __future__ import annotations
import logging
import datetime
import typing

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
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    EntityCategory,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)

from .const import DOMAIN
from .coordinator import KiddeCoordinator
from .entity import KiddeEntity


logger = logging.getLogger(__name__)


_TIMESTAMP_DESCRIPTIONS = (
    SensorEntityDescription(
        key="last_seen",
        icon="mdi:home-clock",
        name="Last Seen",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="last_test_time",
        icon="mdi:home-clock",
        name="Last Test Time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="iaq_last_test_time",
        icon="mdi:home-clock",
        name="IAQ Last Test Time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)

_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="overall_iaq_status",
        icon="mdi:air-filter",
        name="Overall Air Quality",
        device_class=SensorDeviceClass.ENUM,
        options=["Very Bad", "Bad", "Moderate", "Good"],
    ),
    SensorEntityDescription(
        key="smoke_level",
        icon="mdi:smoke",
        name="Smoke Level",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.AQI,
    ),
    SensorEntityDescription(
        key="co_level",
        icon="mdi:molecule-co",
        name="CO Level",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CO,
    ),
    SensorEntityDescription(
        key="batt_volt",
        icon="mdi:battery",
        name="Battery Voltage",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="life",
        icon="mdi:calendar-clock",
        name="Weeks to replace",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.WEEKS,
    ),
    SensorEntityDescription(
        key="ap_rssi",
        icon="mdi:wifi-strength-3",
        name="Signal strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="ssid",
        icon="mdi:wifi",
        name="SSID",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)

_MEASUREMENTSENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="iaq_temperature",
        name="Indoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="hpa",
        name="Air Pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="tvoc",
        name="Total VOC",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="iaq",
        name="Indoor Air Quality",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="co2",
        name="CO₂ Level",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
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
    or '2024-06-22T16:00:19Z' which needs to be converted to a python datetime.
    """

    @property
    def native_value(self) -> datetime.datetime | None:
        """Return the native value of the sensor."""
        value = self.kidde_device.get(self.entity_description.key)
        dtype = type(value)
        logger.debug(
            "%s, of type %s is %s",
            self.entity_description.key,
            dtype,
            value,
        )
        if value is None:
            return value
        # Last seen and last test return different precision for time, so we
        # need to strip anything beyond microseconds
        # https://github.com/tache/homeassistant-kidde/issues/7
        stripped = value.strip("Z").split(".")[0]
        return datetime.datetime.strptime(stripped, "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=datetime.timezone.utc
        )


class KiddeSensorEntity(KiddeEntity, SensorEntity):
    """Sensor for Kidde HomeSafe."""

    @property
    def native_value(self) -> str | None | float | int:
        """Return the native value of the sensor."""
        value = self.kidde_device.get(self.entity_description.key)
        dtype = type(value)
        logger.debug(
            "%s, of type %s is %s",
            self.entity_description.key,
            dtype,
            value,
        )
        return value


class KiddeSensorMeasurementEntity(KiddeEntity, SensorEntity):
    """Measurement Sensor for Kidde HomeSafe.

    We expect the Kidde API to report sensor output as a dictionary containing
    a float or intenger value, a string qualitative status string, and a units
    string. For example: "tvoc": { "value": 605.09, "status": "Moderate",
    "Unit": "ppb"}.

    """

    @property
    def state_class(self) -> str:
        """Return the state class of sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> typing.Union[float, None]:
        """Return the native value of the sensor."""
        entity_dict = self.kidde_device.get(self.entity_description.key)
        new_dict = None
        if isinstance(entity_dict, dict):
            new_dict = entity_dict.get("value")
        else:
            ktype = type(entity_dict)
            logger.warning(
                "Unexpected type [%s], expected entity dict for [%s]",
                ktype,
                self.entity_description.key,
            )
            new_dict = None
        return new_dict

    @property
    def native_unit_of_measurement(self) -> typing.Union[str, None]:
        """Return the native unit of measurement of the sensor."""
        entity_dict = self.kidde_device.get(self.entity_description.key)
        measurement_unit = None

        if isinstance(entity_dict, dict):
            entity_unit = entity_dict.get("Unit", "").upper()
            match entity_unit:
                case "C":
                    measurement_unit = UnitOfTemperature.CELSIUS
                case "F":
                    measurement_unit = UnitOfTemperature.FAHRENHEIT
                case "%RH":
                    measurement_unit = PERCENTAGE
                case "HPA":
                    measurement_unit = UnitOfPressure.HPA
                case "PPB":
                    measurement_unit = CONCENTRATION_PARTS_PER_BILLION
                case "PPM":
                    measurement_unit = CONCENTRATION_PARTS_PER_MILLION
                case "V":
                    measurement_unit = UnitOfElectricPotential.VOLT
                case _:
                    measurement_unit = None

        else:
            ktype = type(entity_dict)
            logger.warning(
                "Unexpected type [%s], expected entity dict for [%s]",
                ktype,
                self.entity_description.key,
            )
            measurement_unit = None
        return measurement_unit

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes for the value sensor (Status)."""
        entity_dict = self.kidde_device.get(self.entity_description.key)
        attribute_dict = None
        if isinstance(entity_dict, dict):
            attribute_dict = {"Status": entity_dict.get("status")}
        else:
            ktype = type(entity_dict)
            logger.warning(
                "Unexpected type [%s], expected state attributes dict for [%s]",
                ktype,
                self.entity_description.key,
            )
            attribute_dict = {"Status": None}
        return attribute_dict
