"""Allowlist-only diagnostics; never export account or vehicle identifiers."""


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    vehicles = data.get("vehicles", {})
    return {
        "last_update_success": coordinator.last_update_success,
        "vehicle_count": len(vehicles),
        "eligibility_known_count": sum(bool(v.get("eligibility_known")) for v in vehicles.values()),
        "sections_available": data.get("sections", {}),
    }
