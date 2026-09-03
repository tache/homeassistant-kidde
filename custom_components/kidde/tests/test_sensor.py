"""Tests for the Kidde HomeSafe sensor platform."""

from unittest.mock import MagicMock

import pytest

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
