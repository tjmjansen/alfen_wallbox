"""Class representing a Alfen Wallbox update coordinator."""

import asyncio
from datetime import timedelta
import logging
import ssl

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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .alfen import AlfenDevice
from .const import (
    CONF_REFRESH_CATEGORIES,
    DEFAULT_REFRESH_CATEGORIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

type AlfenConfigEntry = ConfigEntry[AlfenCoordinator]


class AlfenCoordinator(DataUpdateCoordinator[None]):
    """Alfen update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: AlfenConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )

        self.entry = entry
        self.hass = hass
        self.device = None
        self.timeout = self.entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self.hass.async_create_task(self._async_setup())

    async def _async_setup(self):
        """Set up the coordinator."""
        session = async_get_clientsession(self.hass, verify_ssl=False)

        # Default ciphers needed as of python 3.10
        context = ssl.create_default_context()
        # todo: fix Detected blocking call to load_default_certs with
        # context = await self.create_ssl_context()

        context.set_ciphers("DEFAULT")
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        self.device = AlfenDevice(
            session,
            self.entry.data[CONF_HOST],
            self.entry.data[CONF_NAME],
            self.entry.data[CONF_USERNAME],
            self.entry.data[CONF_PASSWORD],
            self.entry.options.get(CONF_REFRESH_CATEGORIES, DEFAULT_REFRESH_CATEGORIES),
            context,
        )
        if not await self.async_connect():
            raise UpdateFailed("Error communicating with API")

    #    async def create_ssl_context(self) -> ssl.SSLContext:
    #        """Create and return an SSL context."""
    #        loop = asyncio.get_running_loop()
    #        return await loop.run_in_executor(None, ssl.create_default_context)

    async def _async_update_data(self) -> None:
        """Fetch data from API endpoint."""

        await asyncio.wait_for(self.device.async_update(), timeout=self.timeout)
        if not await self.device.async_update():
            raise UpdateFailed("Error updating")

        self.device.get_number_of_socket()
        self.device.get_licenses()

    async def async_connect(self) -> bool:
        """Connect to the API endpoint."""

        try:
            async with asyncio.timeout(self.timeout):
                return await self.device.init()
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
    coordinator = entry.runtime_data
    coordinator.device.get_static_properties = True
    coordinator.device.category_options = entry.options.get(
        CONF_REFRESH_CATEGORIES, DEFAULT_REFRESH_CATEGORIES
    )

    coordinator.update_interval = timedelta(
        seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
