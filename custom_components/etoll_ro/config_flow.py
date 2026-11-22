"""Configure a private eToll account locally in Home Assistant."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AuthenticationError, EtollClient, EtollError, UnsupportedAuthentication
from .const import DOMAIN

SCHEMA = vol.Schema({vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str})


class EtollConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._configure("user", user_input)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        return await self._configure("reauth_confirm", user_input)

    async def _configure(self, step, user_input):
        errors = {}
        if user_input is not None:
            client = EtollClient(
                async_get_clientsession(self.hass), user_input[CONF_USERNAME].strip(), user_input[CONF_PASSWORD]
            )
            try:
                profile = await client.profile()
                await client.snapshot(profile["id"])
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except UnsupportedAuthentication:
                errors["base"] = "unsupported_auth"
            except EtollError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(profile["id"])
                data = {**user_input, CONF_USERNAME: user_input[CONF_USERNAME].strip(), "profile_id": profile["id"]}
                if step == "reauth_confirm":
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=profile["name"], data=data)
        return self.async_show_form(step_id=step, data_schema=SCHEMA, errors=errors)
