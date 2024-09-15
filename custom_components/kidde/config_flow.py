"""Config flow for Kidde HomeSafe integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from kidde_homesafe import KiddeClient, KiddeClientAuthError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
        vol.Required("update_interval_seconds", default=30): int,
    }
)


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kidde HomeSafe."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                client = await KiddeClient.from_login(
                    user_input["email"], user_input["password"]
                )
            except KiddeClientAuthError:
                errors["base"] = "invalid_auth"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception(f"{type(e).__name__}: {e}")
                errors["base"] = "unknown"
            else:
                update_interval = user_input["update_interval_seconds"]
                if isinstance(update_interval, int) and update_interval >= 5:
                    title = f"Kidde ({user_input['email']})"
                    data = {
                        "cookies": client.cookies,
                        "update_interval": update_interval,
                    }
                    return self.async_create_entry(title=title, data=data)
                errors["base"] = "invalid_update_interval"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
