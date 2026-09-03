![Home Assistant](https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white)

[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat)](https://github.com/tache/homeassistant-kidde/blob/master/LICENSE)
[![Validate](https://github.com/tache/homeassistant-kidde/actions/workflows/validate.yml/badge.svg)](https://github.com/tache/homeassistant-kidde/actions/workflows/validate.yml)

# New Lead Fork
We are continuing the work for this capability, and this fork will takeover as the lead [fork][fork] for this repo.</br>
Thank you to [@865charlesw](https://github.com/865charlesw) for the awesome start to the effort.</br>

# Kidde HomeSafe Integration
_Integration to integrate smart alarm devices with [Kidde HomeSafe][kidde_homesafe]._

Devices supported include
- Smoke + Carbon Monoxide Alarm with Indoor Air Quality Monitor (P4010ACSCOAQ-WF) (verified)
- Smoke Alarm with Indoor Air Quality Monitor (P4010ACSAQ-WF) (verified)
- Smoke + Carbon Monoxide Alarm with smart features (P4010ACSCO-WF)
- Smoke Alarm with smart features (P4010ACS-WF) (verified)
- Water Leak + Freeze Detector (60WLDR-W) (verified)
- Carbon Monoxide Alarm with Indoor Air Quality Monitor (KN-COP-DP-10YL-AQ-WF) (verified)

## HACS Installation

1. Follow the [HACS instructions][hacs_custom_repo] for a custom repo, using https://github.com/tache/homeassistant-kidde as the URL
2. The **Kidde HomeSafe** integration should now show up in HACS; click on it and select **Download** --> **Download**
3. Restart Home Assistant
4. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Kidde"
5. Configuration is done in the UI

You may get a notification from the Kidde app once you complete setup; either ignore or `ALLOW` it. Selecting `DENY` may prevent this integration from updating.

<!---->

## Configuration

### Update Interval

During setup, you can configure how often the integration polls the Kidde API for updates:

- **Default**: 30 seconds
- **Minimum**: 5 seconds
- **Recommended**: 30-60 seconds for most use cases

**Note**: Setting a very low update interval (below 10 seconds) may:
- Increase your Home Assistant's CPU usage
- Generate more API calls to Kidde's servers
- Potentially trigger rate limiting (though not currently observed)

You can adjust this setting by:
1. Go to Settings → Devices & Services
2. Find "Kidde HomeSafe" and click "Configure"
3. Adjust the "Update Interval (seconds)" field

## Troubleshooting

### Connection Errors or Authentication Issues

If you see errors like `Cannot connect to host api.homesafe.kidde.com` or authentication failures:

1. **Go to Settings → Devices & Services**
2. **Find "Kidde HomeSafe" in your integrations list**
3. **Click the three dots (⋮) on the Kidde integration**
4. **Select "Reconfigure"** (or "Configure" if available)
5. **Re-enter your credentials** to refresh authentication

**Alternative - Delete and Re-add:**

If "Reconfigure" isn't available:
1. Settings → Devices & Services
2. Find "Kidde HomeSafe" and click the three dots (⋮)
3. Select "Delete"
4. Click "+ Add Integration"
5. Search for "Kidde" and re-add with your credentials

This refreshes your authentication tokens and should resolve most connection issues.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[hacs_custom_repo]: https://hacs.xyz/docs/faq/custom_repositories/
[kidde_homesafe]: https://github.com/865charlesw/kidde-homesafe
[fork]: https://github.com/tache/homeassistant-kidde
