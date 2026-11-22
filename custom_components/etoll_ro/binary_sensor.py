"""Explicit validity state; unavailable data is never treated as invalid."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.util import dt as dt_util

from .entity import VehicleEntity, discover


async def async_setup_entry(hass, entry, async_add_entities):
    discover(entry, async_add_entities, lambda c, v: [VignetteValid(c, v), VehicleInformation(c, v)])


class VignetteValid(VehicleEntity, BinarySensorEntity):
    _attr_translation_key = "vignette_valid"
    _attr_icon = "mdi:ticket-confirmation"

    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "vignette_valid")

    @property
    def is_on(self):
        if not self.vehicle.get("eligibility_known"):
            return None
        expiry = self.vehicle.get("expires_at")
        return expiry is not None and dt_util.utcnow() <= expiry


class VehicleInformation(VehicleEntity, BinarySensorEntity):
    _attr_translation_key = "vehicle_data_problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "vehicle_data_problem")

    @property
    def is_on(self):
        valid = self.vehicle.get("data_valid")
        return None if valid is None else not valid

    @property
    def extra_state_attributes(self):
        fields = {
            "plateNumber": "plate_number",
            "vin": "vin",
            "registrationSerial": "registration_certificate",
            "emissionStandard": "emission_standard",
            "countryCode": "country_code",
            "mtma": "maximum_mass_kg",
            "strrPeajCategoryCode": "bridge_category",
            "temporaryPlate": "temporary_plate",
            "favorite": "favorite",
            "vehicleType": "vehicle_type",
        }
        return {fields[k]: v for k, v in self.vehicle.get("details", {}).items()}
