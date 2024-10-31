"""Entity representing a Jewish Calendar sensor."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LANGUAGE, CONF_LOCATION
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from . import JCalConfigEntry
from .const import (
    CONF_CANDLE_LIGHT_MINUTES,
    CONF_DIASPORA,
    CONF_HAVDALAH_OFFSET_MINUTES,
    DOMAIN,
)


class JewishCalendarEntity(Entity):
    """An HA implementation for Jewish Calendar entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: JCalConfigEntry,
        description: EntityDescription,
    ) -> None:
        """Initialize a Jewish Calendar entity."""
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
        )
        data = config_entry.runtime_data
        self._location = data.location
        self._hebrew = data.language == "hebrew"
        self._candle_lighting_offset = data.candle_lighting_offset
        self._havdalah_offset = data.havdalah_offset
        self._diaspora = data.diaspora
