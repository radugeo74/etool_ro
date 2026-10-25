"""Vehicle category, expiry timestamp, and formatted local expiration."""

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.util import dt as dt_util

from .const import VEHICLE_CATEGORY_LABELS
from .entity import AccountEntity, VehicleEntity, discover
from .models import LOCAL_ZONE, next_bridge_expiration


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            AccountSensor(entry.runtime_data, key)
            for key in (
                "notifications",
                "service_status",
                "latest_invoice",
                "paid_this_year",
                "vehicle_count",
                "last_successful_update",
            )
        ]
    )
    discover(
        entry,
        async_add_entities,
        lambda c, v: (
            [EtollSensor(c, v, key) for key in ("category", "expires_at", "days_remaining")]
            + [VehicleServiceSensor(c, v, key) for key in ("spending", "bridge_remaining", "next_bridge_expiration")]
        ),
    )


class EtollSensor(VehicleEntity, SensorEntity):
    def __init__(self, coordinator, vehicle_id, key):
        super().__init__(coordinator, vehicle_id, key)
        self.key = key
        self._attr_translation_key = key
        if key == "expires_at":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        elif key == "days_remaining":
            # Keep the original unique ID so existing dashboard cards still work.
            # Text preserves the exact requested format regardless of UI locale.
            self._attr_device_class = None
            self._attr_icon = "mdi:calendar-check"
        else:
            self._attr_icon = "mdi:car"

    @property
    def native_value(self):
        if self.key == "category":
            category = self.vehicle.get("category")
            return VEHICLE_CATEGORY_LABELS.get(category, category) if isinstance(category, str) else None
        expiry = self.vehicle.get("expires_at")
        if self.key == "expires_at" or expiry is None:
            return expiry
        return expiry.astimezone(LOCAL_ZONE).strftime("%d/%m/%Y %H:%M")

    @property
    def extra_state_attributes(self):
        if self.key == "category":
            return {"category_code": self.vehicle.get("category")}
        if self.key == "expires_at":
            details = self.vehicle.get("services", {}).get("current_vignette") or {}
            return {k: v for k, v in details.items() if v is not None}
        return None


class VehicleServiceSensor(VehicleEntity, SensorEntity):
    def __init__(self, coordinator, vehicle_id, key):
        super().__init__(coordinator, vehicle_id, key)
        self.key = key
        self._attr_translation_key = key
        if key == "spending":
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_native_unit_of_measurement = "RON"
            self._attr_state_class = SensorStateClass.TOTAL
        else:
            self._attr_icon = "mdi:bridge"

    @property
    def summary(self):
        return self.vehicle.get("services", {})

    @property
    def available(self):
        return (
            super().available
            and self.coordinator.data["sections"].get("services", False)
            and (self.key != "spending" or self.summary.get("year") == dt_util.utcnow().astimezone(LOCAL_ZONE).year)
        )

    @property
    def native_value(self):
        if self.key == "spending":
            return self.summary.get("total")
        if self.key == "next_bridge_expiration":
            expiry = next_bridge_expiration(self.summary.get("bridge_passes", []), dt_util.utcnow())
            return expiry.astimezone(LOCAL_ZONE).strftime("%d/%m/%Y %H:%M") if expiry else None
        return sum(
            p["remaining"]
            for p in self.summary.get("bridge_passes", [])
            if p["valid_until"] is None or dt_util.utcnow() <= p["valid_until"]
        )

    @property
    def extra_state_attributes(self):
        if self.key == "next_bridge_expiration":
            expiry = next_bridge_expiration(self.summary.get("bridge_passes", []), dt_util.utcnow())
            return {"expires_at": expiry.isoformat() if expiry else None}
        keys = (
            (
                "year",
                "vignette_amount",
                "bridge_amount",
                "route_amount",
                "purchase_count",
                "last_purchase",
                "yearly_totals",
            )
            if self.key == "spending"
            else ("bridge_passes",)
        )
        return {k: self.summary[k] for k in keys if self.summary.get(k) is not None}

    @property
    def last_reset(self):
        year = self.summary.get("year")
        return datetime(year, 1, 1, tzinfo=LOCAL_ZONE) if self.key == "spending" and year else None


class AccountSensor(AccountEntity, SensorEntity):
    def __init__(self, coordinator, key):
        super().__init__(coordinator, key)
        self.key = key
        if key in ("latest_invoice", "paid_this_year"):
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_native_unit_of_measurement = "RON"
            if key == "paid_this_year":
                self._attr_state_class = SensorStateClass.TOTAL
        elif key == "service_status":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = ["operational", "performance_issues", "partial_outage", "major_outage"]
        elif key == "last_successful_update":
            self._attr_icon = "mdi:clock-check-outline"
        else:
            self._attr_icon = "mdi:bell" if key == "notifications" else "mdi:car-multiple"

    @property
    def available(self):
        if self.key == "last_successful_update":
            # Retain the previous success time when subsequent updates fail.
            return True
        if not super().available:
            return False
        if self.key == "vehicle_count":
            return True
        section = "invoices" if self.key in ("latest_invoice", "paid_this_year") else self.key
        if not self.coordinator.data["sections"].get(section, False):
            return False
        return (
            self.key != "paid_this_year"
            or self.account["invoices"]["year"] == dt_util.utcnow().astimezone(LOCAL_ZONE).year
        )

    @property
    def native_value(self):
        if self.key == "last_successful_update":
            stamp = self.coordinator.last_successful_update
            return stamp.astimezone(LOCAL_ZONE).strftime("%d/%m/%Y %H:%M") if stamp else None
        if self.key == "vehicle_count":
            return len(self.coordinator.data["vehicles"])
        if self.key == "notifications":
            return self.account.get("notifications")
        if self.key == "service_status":
            return (self.account.get("service_status") or {}).get("state")
        invoices = self.account.get("invoices") or {}
        if self.key == "paid_this_year":
            return invoices.get("total")
        return (invoices.get("latest") or {}).get("amount")

    @property
    def extra_state_attributes(self):
        if self.key == "last_successful_update":
            stamp = self.coordinator.last_successful_update
            data = self.coordinator.data or {}
            return {
                "updated_at": stamp.isoformat() if stamp else None,
                "last_poll_succeeded": self.coordinator.last_update_success,
                "sections_available": data.get("sections", {}) if self.coordinator.last_update_success else {},
            }
        if self.key == "service_status":
            return {k: v for k, v in (self.account.get("service_status") or {}).items() if k != "state"}
        if self.key == "latest_invoice":
            return {
                k: v
                for k, v in ((self.account.get("invoices") or {}).get("latest") or {}).items()
                if k != "amount" and v is not None
            }
        if self.key == "paid_this_year":
            invoices = self.account.get("invoices") or {}
            return {k: v for k, v in invoices.items() if k not in ("total", "latest")}
        return None

    @property
    def last_reset(self):
        year = (self.account.get("invoices") or {}).get("year")
        return datetime(year, 1, 1, tzinfo=LOCAL_ZONE) if self.key == "paid_this_year" and year else None
