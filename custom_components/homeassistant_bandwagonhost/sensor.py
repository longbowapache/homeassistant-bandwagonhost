import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_MONITORED_CONDITIONS, CONF_NAME, EVENT_HOMEASSISTANT_START, DATA_GIGABYTES
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .bwh import BWH

_Log = logging.getLogger(__name__)
DOMAIN = 'homeassistant_bandwagonhost'
REQUIREMENTS = ['requests']
DEFAULT_NAME = '搬瓦工状态'
CONF_VEID = 'veid'
CONF_API_KEY = 'api_key'
MONITORED_CONDITIONS = {
    'VPS_STATE': ['Vps State', '', 'mdi:cloud-search'],
    'CURRENT_BANDWIDTH_USED': ['Current Bandwidth Used', DATA_GIGABYTES,
                               'mdi:cloud-tags'],
    'DISK_USED': ['DISK USED', DATA_GIGABYTES, 'mdi:disc'],
}

SCAN_INTERVAL = timedelta(seconds=1200)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_VEID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS,
                 default=list(MONITORED_CONDITIONS)):
        vol.All(cv.ensure_list, [vol.In(MONITORED_CONDITIONS)])
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Setup the sensor platform."""
    veid = config.get(CONF_VEID)
    api_key = config.get(CONF_API_KEY)
    sensor_name = config.get(CONF_NAME)
    monitored_conditions = config.get(CONF_MONITORED_CONDITIONS)
    bwh = BWH(veid, api_key)
    sensors = []
    for condition in monitored_conditions:
        sensors.append(BandwagonHostSensor(sensor_name, veid, api_key, condition, bwh))

    async_add_entities(sensors)


class BandwagonHostSensor(Entity):

    def __init__(self, sensor_name, veid, api_key, condition, bwh: BWH):

        self.attributes = {}
        self._state = None
        self._name = sensor_name
        self._condition = condition
        self._veid = veid
        self._api_key = api_key

        condition_info = MONITORED_CONDITIONS[condition]

        self._condition_name = condition_info[0]
        self._units = condition_info[1]
        self._icon = condition_info[2]
        self.entity_id = f'{DOMAIN}.{self._veid}_{self._condition}'
        self._bwh = bwh

    async def async_added_to_hass(self):
        """Set initial state."""

        @callback
        def on_startup(_):
            self.async_schedule_update_ha_state(True)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, on_startup)

    @property
    def name(self):
        """Return the name of the sensor."""
        try:
            return self._name.format(self._condition_name)
        except IndexError:
            try:
                return self._name.format(
                    self.data['label'], self._condition_name)
            except (KeyError, TypeError):
                return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """返回图标."""
        return self._icon

    @property
    def unique_id(self):
        return self.entity_id

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attributes

    @property
    def unit_of_measurement(self):
        return self._units

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            if self._condition == 'CURRENT_BANDWIDTH_USED':
                self._state = self._bwh.used_bandwidth
            elif self._condition == 'DISK_USED':
                self._state = self._bwh.disk_used
            elif self._condition == 'VPS_STATE':
                self._state = self._bwh.state
            else:
                self._state = "something wrong"
        except ConnectionError:
            _Log.error("搬瓦工：连接错误，请检查网络")
