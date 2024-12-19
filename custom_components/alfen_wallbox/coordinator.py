"""Class representing a Alfen Wallbox update coordinator."""

import asyncio
import logging
from datetime import timedelta

from aiohttp import ClientConnectionError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .alfen import AlfenDevice
from .const import CONF_TRANSACTION_DATA, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type AlfenConfigEntry = ConfigEntry[AlfenCoordinator]


class AlfenCoordinator(DataUpdateCoordinator[None]):
    """Alfen update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: AlfenConfigEntry) -> None:
        """Initialize the coordinator."""
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        self.entry = entry
        session = async_get_clientsession(hass, verify_ssl=False)
        session.connector._keepalive_timeout = 2 * scan_interval

        self.device = AlfenDevice(
            session,
            entry.data[CONF_HOST],
            entry.data[CONF_NAME],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.options[CONF_TRANSACTION_DATA],
        )

    async def _async_update_data(self) -> None:
        """Fetch data from API endpoint."""

        if not self.device.id:
            if not await self.async_connect():
                return False

        await self.device.async_update()
        self.device.get_number_of_socket()
        self.device.get_licenses()

        return True

    async def async_connect(self) -> bool:
        """Connect to the API endpoint."""

        try:
            async with asyncio.timeout(self.entry.options[CONF_TIMEOUT]):
                self.device.initilize = True
                await self.device.init()
                self.device.initilize = False
                if not self.device.id:
                    return False
                return True
        except TimeoutError:
            _LOGGER.debug("Connection to %s timed out", self.entry.data[CONF_HOST])
            return False
        except ClientConnectionError as e:
            _LOGGER.debug(
                "ClientConnectionError to %s %s",
                self.entry.data[CONF_HOST],
                str(e),
            )
            return False
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unexpected error creating device %s %s",
                self.entry.data[CONF_HOST],
                str(e),
            )
            return False


async def options_update_listener(self, entry: AlfenConfigEntry):
    """Handle options update."""
    self.coordinator = entry.runtime_data
    self.coordinator.device.get_transactions = entry.options.get(
        CONF_TRANSACTION_DATA, False
    )

    self.coordinator.update_interval = timedelta(
        seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
