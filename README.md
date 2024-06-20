# New Lead Fork
The @tache fork will takeover as the lead fork [fork][fork] for this repo.
Thank you to @865charlesw for the awesome start to the effort.

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
