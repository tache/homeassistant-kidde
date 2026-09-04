# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-03

### Added
- **New Sensors (13 total)**:
  - `end_of_life_status` - Device lifecycle status (Normal/Warning/Critical) with numeric-to-enum mapping
  - `iaq_state` - IAQ calibration state (Normal/Learning/Calibrating)
  - `iaq_test_status` - IAQ self-test status (boolean)
  - `iaq_learn_countdown` - Days remaining until IAQ calibration complete
  - `cap_sensor` - Sensor capabilities list (e.g., "Smoke, IAQ, CO")
  - `capabilities` - Hardware capabilities list (e.g., "smoke, temperature, co")
  - `mb_model` - Mainboard model number (diagnostic, disabled by default)
  - `temperature_ad` - Raw temperature ADC value (diagnostic, disabled by default)
  - `smoke_comp` - Smoke compensation value (diagnostic, disabled by default)
  - `country_code` - Device country code (diagnostic, disabled by default)
  - `locate_active` - Device locate/find feature status (binary sensor)

- **New Entity Classes**:
  - `KiddeSensorMappedEntity` - Handles numeric- or string-to-enum value conversions
  - `KiddeSensorListEntity` - Handles array/list values as comma-separated strings

- **Button Support**:
  - Added Test and Hush buttons to CO-only detectors (`cowifidetector`)

- **Reauthentication Flow**:
  - Config flow now triggers a reauth dialog automatically when authentication fails
  - Updates stored cookies without requiring the integration to be removed and re-added
  - Preserves the existing `update_interval` setting across reauth

- **`healthy_air` Sensor**:
  - New aggregate air quality score (`score`/`category`, e.g. 87/"Good") for IAQ-capable devices

- **Device Removal**:
  - Devices no longer reported by Kidde can now be removed from Home Assistant's device page
  - Removal is refused for devices Kidde still actively reports, preventing them from silently reappearing

- **EssWFAC Device Support** (@ahuffman):
  - Proper device naming for the EssWFAC smoke + carbon monoxide detector
  - Test and Hush buttons now available for EssWFAC (fixes #125)
  - New `battery_state` sensor (`Good`/`Low`/`Normal`/`Unknown`/`Warning`)
  - Battery-low binary sensor now correctly recognizes `Good`/`Normal` states instead of only `ok`, fixing false low-battery alerts (fixes #101)

- **Documentation**:
  - Added troubleshooting section to README for connection/authentication issues
  - Documented how to reconfigure integration to refresh auth tokens
  - Added Configuration section documenting `update_interval` (default 30s, minimum 5s)

### Changed
- Improved sensor naming for clarity:
  - `cap_sensor` renamed to "Sensor Capabilities"
  - Added "Hardware Capabilities" for `capabilities` field
- Updated device detection logic to support CO-only detectors
- All diagnostic sensors are now disabled by default to reduce UI clutter
- Added `PARALLEL_UPDATES = 1` to sensor, binary_sensor, switch, and button platforms to serialize entity updates

### Fixed
- Entity registry now properly handles new sensors on integration reload
- Improved logging for mapped and list sensor types
- `battery_state` sensor now consistently shows "Good" instead of reverting to
  the raw "ok" value after the first coordinator refresh

### Testing
- Added 14 comprehensive unit tests for new sensor types
- Fixed the pytest-asyncio and custom-integration test configuration so the full
  suite (config flow, init, sensors, device removal) actually runs and passes
- CI now runs `ruff` and `pytest` on every push and pull request, in addition
  to the existing Hassfest and HACS validation
- Added `quality_scale.yaml` tracking Home Assistant integration quality scale progress

## [0.1.2] - Previous Release

(Add previous release notes here if available)
