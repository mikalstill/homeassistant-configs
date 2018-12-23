import datetime
import json
import logging
import os
import urllib.request
import xml.etree.ElementTree as ET

from datetime import timedelta

from homeassistant.const import (
    CONF_NAME, STATE_OK)
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_point_in_utc_time, async_track_utc_time_change)
from homeassistant.util import dt as dt_util


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'bom_forecast'
ENTITY_ID = 'bom_forecast.forecast'

ATTR_ID = 'forecast'
DEFAULT_ID = 'IDN10035'


def setup(hass, config):
    bf = BOM_Forecast(hass)
    bf.point_in_time_listener(dt_util.utcnow())

    hass.services.register(DOMAIN, 'fetch', bf.fetch)

    return True


class BOM_Forecast(Entity):
    entity_id = ENTITY_ID

    def __init__(self, hass):
        """Initialize the bom_forecast."""
        self.hass = hass
        if os.path.exists('/srv/homeassistant/config/bom_forecast.json'):
            with open('/srv/homeassistant/config/bom_forecast.json') as f:
                self._forecast = json.loads(f.read())
        else:
            self._forecast = {}

    @property
    def name(self):
        return 'BOM Forecast'

    @property
    def state(self):
        return STATE_OK

    @property
    def state_attributes(self):
        attrs = {}

        # A sample of how to use this:
        #
        # Today is forecast to be "{{states.bom_forecast.forecast.attributes.today_forecast}}", with a maximum of {{states.bom_forecast.forecast.attributes.today_temp_max}} and {{states.bom_forecast.forecast.attributes.today_rain}} chance of rain.

        now = datetime.datetime.now()
        day_data = self._forecast.get('%04d-%02d-%02d'
                                      %(now.year, now.month, now.day))
        attrs['today_temp_min'] = day_data.get('air_temperature_minimum')
        attrs['today_temp_max'] = day_data.get('air_temperature_maximum')
        attrs['today_rain'] = day_data.get('probability_of_precipitation')
        attrs['today_forecast'] = day_data.get('forecast')

        now += datetime.timedelta(days=1)
        day_data = self._forecast.get('%04d-%02d-%02d'
                                      %(now.year, now.month, now.day))
        attrs['tomorrow_temp_min'] = day_data.get('air_temperature_minimum')
        attrs['tomorrow_temp_max'] = day_data.get('air_temperature_maximum')
        attrs['tomorrow_rain'] = day_data.get('probability_of_precipitation')
        attrs['tomorrow_forecast'] = day_data.get('forecast')

        return attrs

    @callback
    def point_in_time_listener(self, now):
        self.async_schedule_update_ha_state()

        async_track_point_in_utc_time(
            self.hass, self.point_in_time_listener,
            datetime.datetime.now() + timedelta(seconds=30))

    def fetch(self, call):
        id = call.data.get(ATTR_ID, DEFAULT_ID)
        url = 'ftp://ftp.bom.gov.au/anon/gen/fwo/%s.xml' % DEFAULT_ID
        _LOGGER.info('Fetching BOM forecast from %s' % url)
        f = urllib.request.urlopen(url)
        xml = f.read()
        f.close()

        tree = ET.ElementTree(ET.fromstring(xml))
        root = tree.getroot()

        for area in root.findall('forecast/area'):
            if area.attrib.get('type') == 'region':
                # Skip generic placeholder text
                continue

            for child in area:
                d = child.attrib['start-time-local'].split('T')[0]

                self._forecast.setdefault(d, {})
                for subchild in child:
                    self._forecast[d][subchild.attrib['type']] = subchild.text

        self._save()
        self.async_schedule_update_ha_state()

    def _save(self):
        with open('/srv/homeassistant/config/bom_forecast.json', 'w') as f:
            f.write(json.dumps(self._forecast, indent=4, sort_keys=True))

