"""Tests for the Kidde HomeSafe sensor platform."""

import logging
from unittest.mock import MagicMock

import pytest

from custom_components.kidde.const import DOMAIN
from custom_components.kidde.coordinator import KiddeCoordinator, KiddeDataset
from custom_components.kidde.sensor import (
    KiddeSensorEntity,
    KiddeSensorListEntity,
    KiddeSensorMappedEntity,
    KiddeSensorMeasurementEntity,
    KiddeSensorTimestampEntity,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with test data."""
    coordinator = MagicMock(spec=KiddeCoordinator)
    coordinator.data = KiddeDataset(
        locations={},
        devices={
            "device1": {
                "id": 1,
                "label": "Test Device",
                "model": "wifiiaqdetector",
                "serial_number": "TEST123",
                "last_seen": "2025-10-08T20:27:37.063459959Z",
                "end_of_life_status": 1,
                "iaq_state": "Normal",
                "iaq_test_status": True,
                "iaq_learn_countdown": 5,
                "cap_sensor": ["Smoke", "IAQ", "CO"],
                "mb_model": 38,
                "temperature_ad": 1984,
                "smoke_comp": -8,
                "smoke_level": 14,
                "tvoc": {"value": 618.87, "status": "Moderate", "Unit": "ppb"},
                "iaq": {"value": 124.64, "status": "Moderate"},
                "co2": {"value": 1246.43, "status": "Moderate", "Unit": "PPM"},
            }
        },
        events={},
    )
    return coordinator


@pytest.fixture
def mock_entity_description():
    """Create a mock entity description."""
    from homeassistant.components.sensor import SensorEntityDescription

    return SensorEntityDescription(key="test_sensor", name="Test Sensor")


class TestKiddeSensorMappedEntity:
    """Test the KiddeSensorMappedEntity class."""

    @pytest.mark.asyncio
    async def test_mapped_entity_normal_value(self, mock_coordinator):
        """Test mapped entity with normal integer value."""
        from homeassistant.components.sensor import SensorEntityDescription

        description = SensorEntityDescription(
            key="end_of_life_status",
            name="End of Life Status",
        )
        mapping = {0: "Normal", 1: "Normal", 2: "Warning", 3: "Critical"}

        entity = KiddeSensorMappedEntity(
            mock_coordinator, "device1", description, mapping
        )

        assert entity.native_value == "Normal"

    @pytest.mark.asyncio
    async def test_mapped_entity_unmapped_value(self, mock_coordinator):
        """Test mapped entity with unmapped integer value."""
        from homeassistant.components.sensor import SensorEntityDescription

        mock_coordinator.data.devices["device1"]["end_of_life_status"] = 99

        description = SensorEntityDescription(
            key="end_of_life_status",
            name="End of Life Status",
        )
        mapping = {0: "Normal", 1: "Normal", 2: "Warning", 3: "Critical"}

        entity = KiddeSensorMappedEntity(
            mock_coordinator, "device1", description, mapping
        )

        assert entity.native_value is None

    @pytest.mark.asyncio
    async def test_mapped_entity_string_key_mapping(self, mock_coordinator):
        """Test mapped entity translates a string raw value via a string-keyed mapping."""
        from homeassistant.components.sensor import SensorEntityDescription

        mock_coordinator.data.devices["device1"]["battery_state"] = "ok"

        description = SensorEntityDescription(
            key="battery_state",
            name="Battery State",
        )
        mapping = {"ok": "Good", "warning": "Warning"}

        entity = KiddeSensorMappedEntity(
            mock_coordinator, "device1", description, mapping
        )

        assert entity.native_value == "Good"

    @pytest.mark.asyncio
    async def test_mapped_entity_unmapped_string_value(self, mock_coordinator):
        """Test mapped entity returns None for a string value with no mapping entry.

        This matters for ENUM sensors: Home Assistant raises if a value outside
        the declared `options` is returned, but silently accepts None as "unknown".
        """
        from homeassistant.components.sensor import SensorEntityDescription

        mock_coordinator.data.devices["device1"]["battery_state"] = "critical"

        description = SensorEntityDescription(
            key="battery_state",
            name="Battery State",
        )
        mapping = {"ok": "Good", "warning": "Warning"}

        entity = KiddeSensorMappedEntity(
            mock_coordinator, "device1", description, mapping
        )

        assert entity.native_value is None

    @pytest.mark.asyncio
    async def test_mapped_entity_reflects_coordinator_refresh(self, mock_coordinator):
        """Test mapped value stays in sync with fresh coordinator data on each poll."""
        from homeassistant.components.sensor import SensorEntityDescription

        mock_coordinator.data.devices["device1"]["battery_state"] = "ok"

        description = SensorEntityDescription(
            key="battery_state",
            name="Battery State",
        )
        mapping = {"ok": "Good", "Low": "Low"}

        entity = KiddeSensorMappedEntity(
            mock_coordinator, "device1", description, mapping
        )

        assert entity.native_value == "Good"

        # Simulate a coordinator refresh that replaces this device's data
        # wholesale, as happens when new data is polled from the API.
        mock_coordinator.data.devices["device1"] = {
            **mock_coordinator.data.devices["device1"],
            "battery_state": "Low",
        }

        assert entity.native_value == "Low"


class TestBatteryStateSetup:
    """Regression coverage for issue #128.

    battery_state must not be normalized by mutating coordinator data once
    at setup, since that mutation is silently overwritten by the next
    coordinator refresh.
    """

    @pytest.mark.asyncio
    async def test_battery_state_mapped_without_mutating_coordinator_data(
        self, mock_coordinator
    ):
        """Battery state should map via the entity, not a setup-time mutation.

        coordinator.data should remain an unmutated mirror of the raw API
        response after async_setup_entry runs.
        """
        from custom_components.kidde.sensor import async_setup_entry

        mock_coordinator.data.devices["device1"]["battery_state"] = "ok"

        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        hass.data = {DOMAIN: {"test_entry": mock_coordinator}}

        added_entities: list = []
        await async_setup_entry(hass, entry, added_entities.extend)

        battery_entity = next(
            e for e in added_entities if e.entity_description.key == "battery_state"
        )
        assert battery_entity.native_value == "Good"
        # The raw API value must be untouched: normalization happens at read
        # time in the entity, not via a one-time mutation during setup.
        assert mock_coordinator.data.devices["device1"]["battery_state"] == "ok"


class TestKiddeSensorListEntity:
    """Test the KiddeSensorListEntity class."""

    @pytest.mark.asyncio
    async def test_list_entity_with_array(self, mock_coordinator):
        """Test list entity with array value."""
        from homeassistant.components.sensor import SensorEntityDescription

        description = SensorEntityDescription(
            key="cap_sensor",
            name="Capabilities",
        )

        entity = KiddeSensorListEntity(mock_coordinator, "device1", description)

        assert entity.native_value == "Smoke, IAQ, CO"

    @pytest.mark.asyncio
    async def test_list_entity_with_non_array(self, mock_coordinator):
        """Test list entity with non-array value."""
        from homeassistant.components.sensor import SensorEntityDescription

        mock_coordinator.data.devices["device1"]["cap_sensor"] = "not_a_list"

        description = SensorEntityDescription(
            key="cap_sensor",
            name="Capabilities",
        )

        entity = KiddeSensorListEntity(mock_coordinator, "device1", description)

        assert entity.native_value is None


class TestKiddeSensorEntity:
    """Test the KiddeSensorEntity class."""

    @pytest.mark.asyncio
    async def test_simple_sensor_integer(self, mock_coordinator):
        """Test simple sensor with integer value."""
        from homeassistant.components.sensor import SensorEntityDescription

        description = SensorEntityDescription(
            key="smoke_level",
            name="Smoke Level",
        )

        entity = KiddeSensorEntity(mock_coordinator, "device1", description)

        assert entity.native_value == 14


class TestKiddeSensorMeasurementEntity:
    """Test the KiddeSensorMeasurementEntity class."""

    @pytest.mark.asyncio
    async def test_measurement_entity_with_value(self, mock_coordinator):
        """Test measurement entity extracts value from dict."""
        from homeassistant.components.sensor import SensorEntityDescription

        description = SensorEntityDescription(
            key="tvoc",
            name="Total VOC",
        )

        entity = KiddeSensorMeasurementEntity(mock_coordinator, "device1", description)

        assert entity.native_value == 618.87

    @pytest.mark.asyncio
    async def test_measurement_entity_unit_conversion(self, mock_coordinator):
        """Test measurement entity converts units correctly."""
        from homeassistant.components.sensor import SensorEntityDescription
        from homeassistant.const import CONCENTRATION_PARTS_PER_BILLION

        description = SensorEntityDescription(
            key="tvoc",
            name="Total VOC",
        )

        entity = KiddeSensorMeasurementEntity(mock_coordinator, "device1", description)

        assert entity.native_unit_of_measurement == CONCENTRATION_PARTS_PER_BILLION

    @pytest.mark.asyncio
    async def test_measurement_entity_unitless_no_warning(
        self, mock_coordinator, caplog
    ):
        """Test a unitless sensor like iaq returns None without a log warning.

        The `iaq` field is unitless by design (see issue #131), so its Unit
        is expected to be absent -- that's not an unrecognized unit. The
        mock_coordinator fixture omits the Unit key entirely for iaq.
        """
        from homeassistant.components.sensor import SensorEntityDescription

        description = SensorEntityDescription(
            key="iaq",
            name="Indoor Air Quality",
        )

        entity = KiddeSensorMeasurementEntity(mock_coordinator, "device1", description)

        with caplog.at_level(logging.DEBUG, logger="custom_components.kidde.sensor"):
            result = entity.native_unit_of_measurement

        assert result is None
        assert "Unknown unit" not in caplog.text

    @pytest.mark.asyncio
    async def test_measurement_entity_unitless_empty_string_no_warning(
        self, mock_coordinator, caplog
    ):
        """Test iaq with an explicit empty-string Unit is also silent.

        Real API captures show both shapes for iaq: some omit the Unit key
        entirely, others include it as "Unit": "". Both must be silent.
        """
        from homeassistant.components.sensor import SensorEntityDescription

        mock_coordinator.data.devices["device1"]["iaq"] = {
            "value": 124.64,
            "status": "Moderate",
            "Unit": "",
        }

        description = SensorEntityDescription(
            key="iaq",
            name="Indoor Air Quality",
        )

        entity = KiddeSensorMeasurementEntity(mock_coordinator, "device1", description)

        with caplog.at_level(logging.DEBUG, logger="custom_components.kidde.sensor"):
            result = entity.native_unit_of_measurement

        assert result is None
        assert "Unknown unit" not in caplog.text

    @pytest.mark.asyncio
    async def test_measurement_entity_empty_unit_still_warns_for_other_keys(
        self, mock_coordinator, caplog
    ):
        """Test an empty unit on a non-iaq field still logs a warning.

        Only `iaq` is unitless by design (see issue #131) -- every other
        measurement field observed in real API data always has a unit, so
        an empty unit there is genuinely unexpected and should still warn.
        """
        from homeassistant.components.sensor import SensorEntityDescription

        mock_coordinator.data.devices["device1"]["tvoc"] = {
            "value": 618.87,
            "status": "Moderate",
            "Unit": "",
        }

        description = SensorEntityDescription(
            key="tvoc",
            name="Total VOC",
        )

        entity = KiddeSensorMeasurementEntity(mock_coordinator, "device1", description)

        with caplog.at_level(logging.DEBUG, logger="custom_components.kidde.sensor"):
            result = entity.native_unit_of_measurement

        assert result is None
        assert "Unknown unit" in caplog.text

    @pytest.mark.asyncio
    async def test_measurement_entity_extra_attributes(self, mock_coordinator):
        """Test measurement entity includes status in extra attributes."""
        from homeassistant.components.sensor import SensorEntityDescription

        description = SensorEntityDescription(
            key="tvoc",
            name="Total VOC",
        )

        entity = KiddeSensorMeasurementEntity(mock_coordinator, "device1", description)

        assert entity.extra_state_attributes == {"Status": "Moderate"}


class TestKiddeSensorTimestampEntity:
    """Test the KiddeSensorTimestampEntity class."""

    @pytest.mark.asyncio
    async def test_timestamp_parsing(self, mock_coordinator):
        """Test timestamp entity parses ISO datetime correctly."""
        from homeassistant.components.sensor import SensorEntityDescription

        description = SensorEntityDescription(
            key="last_seen",
            name="Last Seen",
        )

        entity = KiddeSensorTimestampEntity(mock_coordinator, "device1", description)

        assert entity.native_value is not None
        assert entity.native_value.year == 2025
        assert entity.native_value.month == 10
        assert entity.native_value.day == 8

    @pytest.mark.asyncio
    async def test_timestamp_with_microseconds(self, mock_coordinator):
        """Test timestamp entity handles variable precision."""
        from homeassistant.components.sensor import SensorEntityDescription

        # Test with long fractional seconds
        mock_coordinator.data.devices["device1"][
            "last_seen"
        ] = "2025-10-08T20:27:37.063459959Z"

        description = SensorEntityDescription(
            key="last_seen",
            name="Last Seen",
        )

        entity = KiddeSensorTimestampEntity(mock_coordinator, "device1", description)

        assert entity.native_value is not None
        assert entity.native_value.hour == 20
        assert entity.native_value.minute == 27
        assert entity.native_value.second == 37
