"""Independent Home Assistant integration for eToll România."""

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EtollClient
from .coordinator import EtollCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass, entry):
    client = EtollClient(async_get_clientsession(hass), entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    coordinator = EtollCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
