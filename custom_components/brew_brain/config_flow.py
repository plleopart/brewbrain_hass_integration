"""Config flow for BrewBrain."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry

from .api import BrewBrainAuthenticationError, BrewBrainClient, BrewBrainError
from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN


class BrewBrainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the BrewBrain config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            client = BrewBrainClient(username, password)

            try:
                await client.async_validate_credentials()
            except BrewBrainAuthenticationError:
                errors["base"] = "invalid_auth"
            except BrewBrainError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(username.casefold())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"BrewBrain: {username}",
                    data={CONF_USERNAME: username, CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_credentials_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Start reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm updated BrewBrain credentials."""
        errors: dict[str, str] = {}
        entry: ConfigEntry = self._reauth_entry

        if user_input is not None:
            username = entry.data[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            client = BrewBrainClient(username, password)
            try:
                await client.async_validate_credentials()
            except BrewBrainAuthenticationError:
                errors["base"] = "invalid_auth"
            except BrewBrainError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )


def _credentials_schema(user_input: dict[str, Any] | None) -> vol.Schema:
    """Return the credentials form schema."""
    defaults = user_input or {}
    username_key = vol.Required(CONF_USERNAME)
    if CONF_USERNAME in defaults:
        username_key = vol.Required(CONF_USERNAME, default=defaults[CONF_USERNAME])
    return vol.Schema(
        {
            username_key: str,
            vol.Required(CONF_PASSWORD): str,
        }
    )
