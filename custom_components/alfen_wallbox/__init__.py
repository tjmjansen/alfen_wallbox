"""Alfen Wallbox integration."""

import logging
from typing import Any

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_REFRESH_CATEGORIES,
    DEFAULT_REFRESH_CATEGORIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
)
from .coordinator import AlfenConfigEntry, AlfenCoordinator, options_update_listener

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: AlfenConfigEntry
) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        options = {
            CONF_SCAN_INTERVAL: scan_interval,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_REFRESH_CATEGORIES: DEFAULT_REFRESH_CATEGORIES,
        }
        data = {
            CONF_HOST: config_entry.data.get(CONF_HOST),
            CONF_NAME: config_entry.data.get(CONF_NAME),
            CONF_USERNAME: config_entry.data.get(CONF_USERNAME),
            CONF_PASSWORD: config_entry.data.get(CONF_PASSWORD),
        }

        hass.config_entries.async_update_entry(
            config_entry,
            version=2,
            data=data,
            options=options,
        )

        _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: AlfenConfigEntry
) -> bool:
    """Set up Alfen from a config entry."""
    await er.async_migrate_entries(
        hass, config_entry.entry_id, async_migrate_entity_entry
    )

    coordinator = AlfenCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(
        config_entry.add_update_listener(options_update_listener)
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: AlfenConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry: %s", config_entry)

    coordinator = config_entry.runtime_data
    await coordinator.device.logout()
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


@callback
def async_migrate_entity_entry(
    entity_entry: er.RegistryEntry,
) -> dict[str, Any] | None:
    """Migrate a Alfen entity entry."""

    # No migration needed
    return None
