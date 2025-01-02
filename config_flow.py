import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class BrewBrainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Brew Brain integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        
        errors = {}
        if user_input is not None:
            # Validate the input
            if not user_input["username"] or not user_input["password"]:
                errors["base"] = "auth_error"
            else:
                return self.async_create_entry(title="Brew Brain: " + user_input["username"], data=user_input)

        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )