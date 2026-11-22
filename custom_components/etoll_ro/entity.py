"""Shared vehicle identity and dynamic discovery."""

from datetime import timedelta

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME


class VehicleEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, vehicle_id, key):
        super().__init__(coordinator)
        self.vehicle_id = vehicle_id
        self._attr_unique_id = f"{coordinator.profile_id}_{vehicle_id}_{key}"

    @property
    def vehicle(self):
        return self.coordinator.data["vehicles"].get(self.vehicle_id, {})

    @property
    def available(self):
        return super().available and self.vehicle_id in self.coordinator.data["vehicles"]

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.profile_id}_{self.vehicle_id}")},
            "name": self.vehicle.get("plate", NAME),
            "manufacturer": "CNAIR",
            "model": "Vehicul eToll",
            "via_device": (DOMAIN, self.coordinator.profile_id),
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        # Local time-dependent state must advance even between cloud polls.
        self.async_on_remove(async_track_time_interval(self.hass, self._tick, timedelta(minutes=1)))

    @callback
    def _tick(self, now):
        self.async_write_ha_state()


def discover(entry, async_add_entities, factory):
    coordinator = entry.runtime_data
    known = set()

    @callback
    def updated():
        new_ids = set(coordinator.data["vehicles"]) - known
        known.update(new_ids)
        async_add_entities([entity for vehicle_id in new_ids for entity in factory(coordinator, vehicle_id)])

    updated()
    entry.async_on_unload(coordinator.async_add_listener(updated))


class AccountEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.profile_id}_account_{key}"
        self._attr_translation_key = key

    @property
    def account(self):
        return self.coordinator.data["account"]

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.profile_id)},
            "name": "eToll — Cont",
            "manufacturer": "CNAIR",
            "model": "Cont eToll",
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_track_time_interval(self.hass, self._tick, timedelta(minutes=1)))

    @callback
    def _tick(self, now):
        self.async_write_ha_state()
