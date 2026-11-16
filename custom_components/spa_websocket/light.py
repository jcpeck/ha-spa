"""The spa light, on or off, confirmed off the panel's own LED."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SpaConnection


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the spa light, on the BT-200 only.

    The WF-100 has no known light code, so an entity there could only ever fail.
    """
    connection: SpaConnection = hass.data[DOMAIN][entry.entry_id]
    if connection.transport.is_panel:
        async_add_entities([SpaLight(connection, entry)])


class SpaLight(LightEntity):
    """The light, read from the LED in every display frame.

    Always available, like the other entities: its state is the light as of the
    last frame, and ``read_at`` says when that was.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "Light"
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, connection: SpaConnection, entry: ConfigEntry) -> None:
        self._connection = connection
        self._attr_unique_id = f"{entry.entry_id}_light"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Spa",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to updates."""
        self.async_on_remove(self._connection.add_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool | None:
        """Return the light LED from the last display frame, if any."""
        return self._connection.light_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Say how old the reading is."""
        read_at = self._connection.display_at
        return {"read_at": read_at.isoformat() if read_at else None}

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, pressing only if it is off."""
        await self._connection.async_set_light(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off, pressing only if it is on."""
        await self._connection.async_set_light(False)
