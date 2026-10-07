"""Covers / shutters (WHO 2)."""
from __future__ import annotations

from collections.abc import Callable

from OWNd.message import OWNAutomationCommand, OWNAutomationEvent
from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ADVANCED,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NAME,
    CONF_WHERE,
    OPTIONS_DEVICES,
    SUBENTRY_COVER,
)
from .entity import MyHOMEEntity

TRAVEL_SECONDS = 180
# False: even a STOP leaves the last-direction countdown running.
CANCEL_ON_STOP = True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coord = entry.runtime_data
    async_add_entities(
        MyHOMECover(coord, dev["id"], dev)
        for dev in entry.options.get(OPTIONS_DEVICES, [])
        if dev.get("type") == SUBENTRY_COVER
    )


class MyHOMECover(MyHOMEEntity, CoverEntity):
    def __init__(self, coordinator, device_id: str, data: dict) -> None:
        super().__init__(
            coordinator,
            device_id,
            who=2,
            where=data[CONF_WHERE],
            name=data[CONF_NAME],
            manufacturer=data.get(CONF_MANUFACTURER, ""),
            model=data.get(CONF_MODEL, ""),
        )
        self._advanced = bool(data.get(CONF_ADVANCED, True))
        feat = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        if self._advanced:
            feat |= CoverEntityFeature.SET_POSITION
        self._attr_supported_features = feat
        self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_is_closed = None
        self._attr_current_cover_position = None
        self._attr_is_opening = False
        self._attr_is_closing = False
        self._finish_cancel: Callable[[], None] | None = None

    @callback
    def _cancel_finish(self) -> None:
        if self._finish_cancel is not None:
            self._finish_cancel()
            self._finish_cancel = None

    @callback
    def _start_finish(self, opening: bool) -> None:
        self._cancel_finish()
        # A basic actuator reports direction, not the actual position.
        self._attr_is_closed = None
        self._attr_current_cover_position = None

        @callback
        def finish(_now) -> None:
            self._finish_cancel = None
            self._attr_is_opening = False
            self._attr_is_closing = False
            self._attr_is_closed = not opening
            self._attr_current_cover_position = 100 if opening else 0
            self.async_write_ha_state()

        self._finish_cancel = async_call_later(self.hass, TRAVEL_SECONDS, finish)

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_finish()
        await super().async_will_remove_from_hass()

    async def async_request_initial_state(self) -> None:
        await self._coordinator.send_status_request(OWNAutomationCommand.status(self._where))

    async def async_open_cover(self, **_) -> None:
        await self._coordinator.send(OWNAutomationCommand.raise_shutter(self._where))

    async def async_close_cover(self, **_) -> None:
        await self._coordinator.send(OWNAutomationCommand.lower_shutter(self._where))

    async def async_stop_cover(self, **_) -> None:
        await self._coordinator.send(OWNAutomationCommand.stop_shutter(self._where))

    async def async_set_cover_position(self, **kwargs) -> None:
        if ATTR_POSITION in kwargs:
            await self._coordinator.send(
                OWNAutomationCommand.set_shutter_level(self._where, kwargs[ATTR_POSITION])
            )

    def handle_event(self, message: OWNAutomationEvent) -> None:
        if message.is_opening is not None:
            self._attr_is_opening = message.is_opening
        if message.is_closing is not None:
            self._attr_is_closing = message.is_closing
        if not self._advanced:
            if message.is_opening is True or message.is_closing is True:
                self._start_finish(opening=message.is_opening is True)
            elif (
                message.is_opening is False
                and message.is_closing is False
                and self._finish_cancel is not None
                and CANCEL_ON_STOP
            ):
                self._cancel_finish()
                self._attr_is_closed = None
                self._attr_current_cover_position = None
        if message.is_closed is not None:
            self._attr_is_closed = message.is_closed
        if message.current_position is not None:
            self._attr_current_cover_position = message.current_position
        self.async_write_ha_state()
