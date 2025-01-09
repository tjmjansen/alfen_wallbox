"""Diagnostics support for Alfen."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import AlfenConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: AlfenConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    device = entry.runtime_data.device
    return {
        "id": device.id,
        "name": device.name,
        "info": vars(device.info),
        "keep_logout": device.keep_logout,
        "max_allowed_phases": device.max_allowed_phases,
        "number_socket": device.get_number_of_sockets(),
        "licenses": device.get_licenses(),
        "category_options": device.category_options,
        "properties": device.properties,
    }
