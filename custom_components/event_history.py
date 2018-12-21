import datetime
import json
import logging
import os
import time

from datetime import timedelta

from homeassistant.const import (
    CONF_NAME, STATE_OK)
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_point_in_utc_time, async_track_utc_time_change)
from homeassistant.util import dt as dt_util


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'event_history'
ENTITY_ID = 'event_history.events'

ATTR_NAME = 'name'
DEFAULT_NAME = 'default'


def setup(hass, config):
    eh = Event_History(hass)
    eh.point_in_time_listener(dt_util.utcnow())

    hass.services.register(DOMAIN, 'record_event', eh.record_event)

    return True


class Event_History(Entity):
    entity_id = ENTITY_ID

    def __init__(self, hass):
        """Initialize the event_history."""
        self.hass = hass
        if os.path.exists('/srv/homeassistant/config/event_history.json'):
            with open('/srv/homeassistant/config/event_history.json') as f:
                self._events = json.loads(f.read())
        else:
            self._events = {}
        self._events['started'] = self._events['updated'] = time.time()
        self._save()

        async_track_utc_time_change(hass, self.timer_update, second=30)

    @property
    def name(self):
        return 'Event History'

    @property
    def state(self):
        return STATE_OK

    @property
    def state_attributes(self):
        self._save()
        return self._events

    @callback
    def update_event_history(self, utc_point_in_time):
        self._save()

    @callback
    def point_in_time_listener(self, now):
        self.update_event_history(now)
        self.async_schedule_update_ha_state()

        async_track_point_in_utc_time(
            self.hass, self.point_in_time_listener,
            datetime.datetime.now() + timedelta(seconds=30))

    @callback
    def timer_update(self, time):
        self.update_event_history(time)
        self.async_schedule_update_ha_state()

    def record_event(self, call):
        name = call.data.get(ATTR_NAME, DEFAULT_NAME)
        self._events[name] = time.time()
        self._save(dirty=True)
        _LOGGER.info('Event %s recorded at %s' %(name, time.time()))
        self.async_schedule_update_ha_state()

    def _save(self, dirty=False):
        age = time.time() - self._events['updated']
        self._events['updated'] = time.time()

        if not dirty and age < 1800:
            return

        with open('/srv/homeassistant/config/event_history.json', 'w') as f:
            f.write(json.dumps(self._events, indent=4, sort_keys=True))
