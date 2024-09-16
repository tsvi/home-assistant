"""Tests for the Jewish Calendar calendar platform."""

from homeassistant.core import HomeAssistant

from . import MockConfigEntry


async def test_calendar_exists(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test that the calendar exists."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    state = hass.states.get("calendar.jewish_calendar_user_events")
    assert state

def test_create_event():
    """Test creating an event."""

def test_update_event():
    """Test updating an event."""

def test_delete_event():
    """Test deleting an event."""
