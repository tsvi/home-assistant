"""Platform to retrieve Jewish calendar information for Home Assistant."""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "date": ["Date", "mdi:judaism"],
    "weekly_portion": ["Parshat Hashavua", "mdi:book-open-variant"],
    "holiday_name": ["Holiday", "mdi:calendar-star"],
    "first_light": ["Alot Hashachar", "mdi:weather-sunset-up"],
    "gra_end_shma": ['Latest time for Shm"a GR"A', "mdi:calendar-clock"],
    "mga_end_shma": ['Latest time for Shm"a MG"A', "mdi:calendar-clock"],
    "plag_mincha": ["Plag Hamincha", "mdi:weather-sunset-down"],
    "first_stars": ["T'set Hakochavim", "mdi:weather-night"],
    "upcoming_shabbat_candle_lighting": [
        "Upcoming Shabbat Candle Lighting",
        "mdi:candle",
    ],
    "upcoming_shabbat_havdalah": ["Upcoming Shabbat Havdalah", "mdi:weather-night"],
    "upcoming_candle_lighting": ["Upcoming Candle Lighting", "mdi:candle"],
    "upcoming_havdalah": ["Upcoming Havdalah", "mdi:weather-night"],
    "issur_melacha_in_effect": ["Issur Melacha in Effect", "mdi:power-plug-off"],
    "omer_count": ["Day of the Omer", "mdi:counter"],
}

CONF_DIASPORA = "diaspora"
CONF_LANGUAGE = "language"
CONF_SENSORS = "sensors"
CONF_CANDLE_LIGHT_MINUTES = "candle_lighting_minutes_before_sunset"
CONF_HAVDALAH_OFFSET_MINUTES = "havdalah_minutes_after_sunset"

CANDLE_LIGHT_DEFAULT = 18

DEFAULT_NAME = "Jewish Calendar"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DIASPORA, default=False): cv.boolean,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_LANGUAGE, default="english"): vol.In(["hebrew", "english"]),
        vol.Optional(CONF_CANDLE_LIGHT_MINUTES, default=CANDLE_LIGHT_DEFAULT): int,
        # Default of 0 means use 8.5 degrees / 'three_stars' time.
        vol.Optional(CONF_HAVDALAH_OFFSET_MINUTES, default=0): int,
        vol.Optional(CONF_SENSORS, default=["date"]): vol.All(
            cv.ensure_list, vol.Length(min=1), [vol.In(SENSOR_TYPES)]
        ),
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Jewish calendar sensor platform."""
    language = config.get(CONF_LANGUAGE)
    name = config.get(CONF_NAME)
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    diaspora = config.get(CONF_DIASPORA)
    candle_lighting_offset = config.get(CONF_CANDLE_LIGHT_MINUTES)
    havdalah_offset = config.get(CONF_HAVDALAH_OFFSET_MINUTES)

    if None in (latitude, longitude):
        _LOGGER.error("Latitude or longitude not set in Home Assistant config")
        return

    dev = []
    for sensor_type in config[CONF_SENSORS]:
        dev.append(
            JewishCalSensor(
                name,
                language,
                sensor_type,
                latitude,
                longitude,
                hass.config.time_zone,
                diaspora,
                candle_lighting_offset,
                havdalah_offset,
            )
        )
    async_add_entities(dev, True)


class JewishCalSensor(Entity):
    """Representation of an Jewish calendar sensor."""

    def __init__(
        self,
        name,
        language,
        sensor_type,
        latitude,
        longitude,
        timezone,
        diaspora,
        candle_lighting_offset=CANDLE_LIGHT_DEFAULT,
        havdalah_offset=0,
    ):
        """Initialize the Jewish calendar sensor."""
        self.client_name = name
        self._name = SENSOR_TYPES[sensor_type][0]
        self.type = sensor_type
        self._hebrew = language == "hebrew"
        self._state = None
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.diaspora = diaspora
        self.candle_lighting_offset = candle_lighting_offset
        self.havdalah_offset = havdalah_offset
        _LOGGER.debug("Sensor %s initialized", self.type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {}".format(self.client_name, self._name)

    @property
    def icon(self):
        """Icon to display in the front end."""
        return SENSOR_TYPES[self.type][1]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Update the state of the sensor."""
        from zmanim.hebrew_calendar.jewish_date import JewishDate
        from zmanim.zmanim_calendar import ZmanimCalendar
        from zmanim.util.geo_location import GeoLocation

        now = dt_util.as_local(dt_util.now())
        _LOGGER.debug("Now: %s Timezone = %s", now, now.tzinfo)

        today = now.date()
        location = GeoLocation('Home', latitude=self.latitude,
                               longitude=self.longitude,
                               time_zone=self.timezone)

        def make_zmanim(date):
            """Create a Zmanim object."""
            return ZmanimCalendar(
                candle_lighting_offset=self.candle_lighting_offset,
                date=date, geo_location=location)

        date = JewishDate(in_israel=not self.diaspora)
        date.set_gregorian_date(*today.timetuple()[:3])

        # The Jewish day starts after darkness (called "tzais") and finishes at
        # sunset ("shkia"). The time in between is a gray area (aka "Bein
        # Hashmashot" - literally: "in between the sun and the moon").

        # For some sensors, it is more interesting to consider the date to be
        # tomorrow based on sunset ("shkia"), for others based on "tzais".
        # Hence the following variables.
        after_tzais_date = after_shkia_date = date
        if now > make_zmanim(today).shkia():
            after_shkia_date = date.forward()

        if now > make_zmanim(today).tzais():
            after_tzais_date = date.forward()

        # Terminology note: by convention in py-libhdate library, "upcoming"
        # refers to "current" or "upcoming" dates.
        if self.type == 'date':
            self._state = after_shkia_date.jewish_date
        elif self.type == 'weekly_portion':
            # Compute the weekly portion based on the upcoming shabbat.
            self._state = after_tzais_date.upcoming_shabbat.parasha
        elif self.type == 'holiday_name':
            self._state = after_shkia_date.significant_day()
        elif self.type == 'upcoming_shabbat_candle_lighting':
            times = make_zmanim(after_tzais_date.gregorian_date)
            self._state = times.candle_lighting()
        elif self.type == 'upcoming_candle_lighting':
            times = make_zmanim(after_tzais_date.gregorian_date)
            self._state = times.candle_lighting()
        elif self.type == 'upcoming_shabbat_havdalah':
            times = make_zmanim(after_tzais_date.gregorian_date)
            self._state = times.tzais()
        elif self.type == 'upcoming_havdalah':
            times = make_zmanim(after_tzais_date.gregorian_date)
            self._state = times.tzais()
        elif self.type == 'issur_melacha_in_effect':
            self._state = make_zmanim(today).is_assur_bemelacha(
                now, in_israel=not self.diaspora)
        elif self.type == "omer_count":
            self._state = date.day_of_omer()
        else:
            self._state = make_zmanim(today)[self.type].time()

        _LOGGER.debug("New value: %s", self._state)
