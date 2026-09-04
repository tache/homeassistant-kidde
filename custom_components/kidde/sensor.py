"""Sensor platform for Kidde Homesafe integration."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KiddeCoordinator
from .entity import KiddeEntity

PARALLEL_UPDATES = 1

# Constants for dictionary keys
KEY_MODEL = "model"
KEY_VALUE = "value"
KEY_STATUS = "status"
KEY_UNIT = "Unit"
KEY_SCORE = "score"
KEY_CATEGORY = "category"
KEY_CAPABILITIES = "capabilities"
KEY_IAQ = "iaq"
KEY_TEMPERATURE = "temperature"

logger = logging.getLogger(__name__)


_LIST_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="cap_sensor",
        icon="mdi:format-list-bulleted",
        name="Sensor Capabilities",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="capabilities",
        icon="mdi:chip",
        name="Hardware Capabilities",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)

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

_MAPPED_SENSOR_DESCRIPTIONS = {
    "end_of_life_status": {
        "description": SensorEntityDescription(
            key="end_of_life_status",
            icon="mdi:calendar-remove",
            name="End of Life Status",
            device_class=SensorDeviceClass.ENUM,
            options=["Normal", "Warning", "Critical"],
        ),
        "mapping": {0: "Normal", 1: "Normal", 2: "Warning", 3: "Critical"},
    },
    "battery_state": {
        "description": SensorEntityDescription(
            key="battery_state",
            icon="mdi:battery-high",
            name="Battery State Detail",
            device_class=SensorDeviceClass.ENUM,
            options=["Good", "Low", "Normal", "Unknown", "Warning"],
        ),
        # API observed returning both title-cased values ("Good", "Low") and
        # lowercase ones ("ok", "warning") for the same field depending on
        # device/firmware. All are mapped explicitly so an ENUM sensor never
        # sees a raw value outside its declared options (which HA validates
        # strictly, raising ValueError on mismatch).
        "mapping": {
            "ok": "Good",
            "warning": "Warning",
            "Good": "Good",
            "Low": "Low",
            "Normal": "Normal",
            "Unknown": "Unknown",
        },
    },
}

_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="overall_iaq_status",
        icon="mdi:air-filter",
        name="Overall Air Quality",
        device_class=SensorDeviceClass.ENUM,
        options=["Very Bad", "Bad", "Moderate", "Good"],
    ),
    SensorEntityDescription(
        key="iaq_state",
        icon="mdi:air-filter",
        name="IAQ State",
        device_class=SensorDeviceClass.ENUM,
        options=["Normal", "Learning", "Calibrating"],
    ),
    SensorEntityDescription(
        key="iaq_test_status",
        icon="mdi:test-tube",
        name="IAQ Test Status",
    ),
    SensorEntityDescription(
        key="iaq_learn_countdown",
        icon="mdi:counter",
        name="IAQ Learn Countdown",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    SensorEntityDescription(
        key="smoke_level",
        icon="mdi:smoke",
        name="Smoke Level",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="co_level",
        icon="mdi:molecule-co",
        name="CO Level",
        state_class=SensorStateClass.MEASUREMENT,
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
    SensorEntityDescription(
        key="alarm_interval",
        icon="mdi:alarm-check",
        name="Alarm Interval",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="alarm_reset_time",
        icon="mdi:alarm-snooze",
        name="Alarm Reset Time",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="battery_level",
        icon="mdi:battery-high",
        name="Battery Level",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_voltage",
        icon="mdi:battery",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SensorEntityDescription(
        key="checkin_interval",
        icon="mdi:clock-check",
        name="Checkin Interval",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.HOURS,
    ),
    SensorEntityDescription(
        key="hold_alarm_time",
        icon="mdi:alarm-plus",
        name="Alarm Hold Time",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rapid_temperature_variation_status",
        icon="mdi:swap-vertical-variant",
        name="Temperature Variation Status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="temperature_variation_value",
        icon="mdi:swap-vertical-variant",
        name="Temperature Variation",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        icon="mdi:home-thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    SensorEntityDescription(
        key="mb_model",
        icon="mdi:chip",
        name="Mainboard Model",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="temperature_ad",
        icon="mdi:thermometer",
        name="Temperature ADC",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="smoke_comp",
        icon="mdi:smoke",
        name="Smoke Compensation",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="country_code",
        icon="mdi:earth",
        name="Country Code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)

_SENSOR_MEASUREMENT_DESCRIPTIONS = (
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

_SENSOR_SCORE_DESCRIPTIONS = (
    SensorEntityDescription(
        key="healthy_air",
        name="Healthy Air Score",
        icon="mdi:air-filter",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: KiddeCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors: list[SensorEntity] = []

    for device_id, device_data in coordinator.data.devices.items():
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Checking model: [%s]",
                coordinator.data.devices[device_id].get(KEY_MODEL, "Unknown"),
            )

        for entity_description in _LIST_SENSOR_DESCRIPTIONS:
            if entity_description.key in device_data:
                sensors.append(
                    KiddeSensorListEntity(coordinator, device_id, entity_description)
                )

        for sensor_key, sensor_config in _MAPPED_SENSOR_DESCRIPTIONS.items():
            if sensor_key in device_data:
                sensors.append(
                    KiddeSensorMappedEntity(
                        coordinator,
                        device_id,
                        sensor_config["description"],
                        sensor_config["mapping"],
                    )
                )

        for entity_description in _TIMESTAMP_DESCRIPTIONS:
            if entity_description.key in device_data:
                sensors.append(
                    KiddeSensorTimestampEntity(
                        coordinator, device_id, entity_description
                    )
                )

        for entity_description in _SENSOR_DESCRIPTIONS:
            if entity_description.key in device_data:
                sensors.append(
                    KiddeSensorEntity(coordinator, device_id, entity_description)
                )

        for entity_description in _SENSOR_MEASUREMENT_DESCRIPTIONS:
            if entity_description.key in device_data:
                sensors.append(
                    KiddeSensorMeasurementEntity(
                        coordinator, device_id, entity_description
                    )
                )

        for entity_description in _SENSOR_SCORE_DESCRIPTIONS:
            if entity_description.key in device_data:
                sensors.append(
                    KiddeSensorScoreEntity(coordinator, device_id, entity_description)
                )

    # NOTE: It is possible that sensors is an empty list. Is that OK?

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
        if logger.isEnabledFor(logging.DEBUG):
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
        try:
            return datetime.datetime.strptime(stripped, "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=datetime.UTC
            )
        except ValueError as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.error("Error parsing datetime '%s': %s", value, e)
            return None


class KiddeSensorMappedEntity(KiddeEntity, SensorEntity):
    """Sensor for Kidde HomeSafe values that need value mapping."""

    def __init__(
        self,
        coordinator: KiddeCoordinator,
        device_id: str,
        entity_description: SensorEntityDescription,
        value_mapping: dict[int, str] | dict[str, str],
    ) -> None:
        """Initialize mapped sensor."""
        super().__init__(coordinator, device_id, entity_description)
        self._value_mapping = value_mapping

    @property
    def native_value(self) -> str | None:
        """Return the mapped value of the sensor."""
        raw_value = self.kidde_device.get(self.entity_description.key)
        if raw_value is None:
            return None
        if isinstance(raw_value, (int, str)):
            mapped = self._value_mapping.get(raw_value)
            if mapped is None and logger.isEnabledFor(logging.DEBUG):
                logger.warning(
                    "No mapping found for %s value %s",
                    self.entity_description.key,
                    raw_value,
                )
            return mapped
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning(
                "Expected int or str for %s, got type %s: %s",
                self.entity_description.key,
                type(raw_value),
                raw_value,
            )
        return None


class KiddeSensorListEntity(KiddeEntity, SensorEntity):
    """Sensor for Kidde HomeSafe list/array values."""

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor as comma-separated string."""
        value = self.kidde_device.get(self.entity_description.key)
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        dtype = type(value)
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning(
                "Expected list for %s, got type %s: %s",
                self.entity_description.key,
                dtype,
                value,
            )
        return None


class KiddeSensorEntity(KiddeEntity, SensorEntity):
    """Sensor for Kidde HomeSafe."""

    @property
    def native_value(self) -> str | None | float | int:
        """Return the native value of the sensor."""
        value = self.kidde_device.get(self.entity_description.key)
        dtype = type(value)
        if logger.isEnabledFor(logging.DEBUG):
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
        """Return the state class of sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        entity_dict = self.kidde_device.get(self.entity_description.key)
        if isinstance(entity_dict, dict):
            sensor_value = entity_dict.get(KEY_VALUE)
        else:
            ktype = type(entity_dict)
            if logger.isEnabledFor(logging.DEBUG):
                logger.warning(
                    "Unexpected type [%s], expected entity dict for [%s]",
                    ktype,
                    self.entity_description.key,
                )
            sensor_value = None
        return sensor_value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the native unit of measurement of the sensor."""
        entity_dict = self.kidde_device.get(self.entity_description.key)

        if not isinstance(entity_dict, dict):
            if logger.isEnabledFor(logging.DEBUG):
                logger.warning(
                    "Unexpected type [%s], expected entity dict for [%s]",
                    type(entity_dict),
                    self.entity_description.key,
                )
            return None

        entity_unit = entity_dict.get(KEY_UNIT, "").upper()

        match entity_unit:
            case "C":
                return UnitOfTemperature.CELSIUS
            case "F":
                return UnitOfTemperature.FAHRENHEIT
            case "%RH":
                return PERCENTAGE
            case "HPA":
                return UnitOfPressure.PA
            case "PPB":
                return CONCENTRATION_PARTS_PER_BILLION
            case "PPM":
                return CONCENTRATION_PARTS_PER_MILLION
            case "V":
                return UnitOfElectricPotential.VOLT
            case _:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.warning(
                        "Unknown unit [%s] for sensor [%s]",
                        entity_unit,
                        self.entity_description.key,
                    )
                return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes for the value sensor (Status)."""
        entity_dict = self.kidde_device.get(self.entity_description.key)
        attribute_dict = None
        if isinstance(entity_dict, dict):
            attribute_dict = {"Status": entity_dict.get(KEY_STATUS)}
        else:
            ktype = type(entity_dict)
            if logger.isEnabledFor(logging.DEBUG):
                logger.warning(
                    "Unexpected type [%s], expected state attributes dict for [%s]",
                    ktype,
                    self.entity_description.key,
                )
            attribute_dict = {"Status": None}
        return attribute_dict


class KiddeSensorScoreEntity(KiddeEntity, SensorEntity):
    """Score Sensor for Kidde HomeSafe.

    We expect the Kidde API to report sensor output as a dictionary containing
    a numeric score and a qualitative category string. For example:
    "healthy_air": { "score": 87, "category": "Good" }.
    """

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        entity_dict = self.kidde_device.get(self.entity_description.key)
        if isinstance(entity_dict, dict):
            return entity_dict.get(KEY_SCORE)
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning(
                "Unexpected type [%s], expected entity dict for [%s]",
                type(entity_dict),
                self.entity_description.key,
            )
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes for the score sensor (Category)."""
        entity_dict = self.kidde_device.get(self.entity_description.key)
        if isinstance(entity_dict, dict):
            return {"Category": entity_dict.get(KEY_CATEGORY)}
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning(
                "Unexpected type [%s], expected state attributes dict for [%s]",
                type(entity_dict),
                self.entity_description.key,
            )
        return {"Category": None}
