![Home Assistant](https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white)

[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat)](https://github.com/tache/homeassistant-kidde/blob/master/LICENSE)
[![Validate](https://github.com/tache/homeassistant-kidde/actions/workflows/validate.yml/badge.svg)](https://github.com/tache/homeassistant-kidde/actions/workflows/validate.yml)

# New Lead Fork
We are continueing the work for this capability, and this fork will takeover as the lead [fork][fork] for this repo.</br>
Thank you to [@865charlesw](https://github.com/865charlesw) for the awesome start to the effort.</br>

# Kidde HomeSafe Integration
_Integration to integrate with [Kidde HomeSafe][kidde_homesafe]._

## HACS Installation

1. Follow the [HACS instructions][hacs_custom_repo] for a custom repo, using https://github.com/tache/homeassistant-kidde as the URL
1. Restart your HomeAssistant instance
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Kidde"
1. Configuration is done in the UI

You may get a notification from the Kidde app once you complete setup; either ignore or `ALLOW` it. Selecting `DENY`` may prevent this integration from updating.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[hacs_custom_repo]: https://hacs.xyz/docs/faq/custom_repositories/
[kidde_homesafe]: https://github.com/865charlesw/kidde-homesafe
[fork]: https://github.com/tache/homeassistant-kidde
