"""Tests for the Jewish Calendar calendar platform."""

from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_calendar_exists(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that the calendar exists."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    state = hass.states.get("calendar.jewish_calendar_user_events")
    assert state


async def test_create_event() -> None:
    """Test creating an event."""


async def test_update_event() -> None:
    """Test updating an event."""


async def test_delete_event() -> None:
    """Test deleting an event."""
