"""Account polling with explicit unavailable/authentication states."""

import logging
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AuthenticationError, EtollError
from .const import DOMAIN, UPDATE_MINUTES
from .models import last_complete_update


class EtollCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=UPDATE_MINUTES),
        )
        self.client = client
        self.profile_id = entry.data["profile_id"]
        self.last_successful_update = None
        self.last_full_update = None

    async def _async_update_data(self):
        try:
            snapshot = await self.client.dashboard(self.profile_id)
            self.last_successful_update = snapshot["updated_at"]
            self.last_full_update = last_complete_update(self.last_full_update, snapshot)
            return snapshot
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Reconnect your eToll account") from err
        except EtollError as err:
            raise UpdateFailed(str(err)) from err
