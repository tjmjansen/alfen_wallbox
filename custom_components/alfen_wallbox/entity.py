"""Base entity for Alfen Wallbox integration."""

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN as ALFEN_DOMAIN
from .coordinator import AlfenConfigEntry, AlfenCoordinator


class AlfenEntity(CoordinatorEntity[AlfenCoordinator], Entity):
    """Define a base Alfen entity."""

    def __init__(self, entry: AlfenConfigEntry) -> None:
        """Initialize the Alfen entity."""

        super().__init__(entry)
        self.coordinator = entry.runtime_data

        self._attr_device_info = DeviceInfo(
            identifiers={(ALFEN_DOMAIN, self.coordinator.device.name)},
            manufacturer="Alfen",
            model=self.coordinator.device.info.model,
            name=self.coordinator.device.name,
            sw_version=self.coordinator.device.info.firmware_version,
        )

    async def async_added_to_hass(self) -> None:
        """Add listener for state changes."""
        await super().async_added_to_hass()
