#!/usr/bin/python

import csv
import datetime
import logging
import os
import re

from datetime import timedelta

from homeassistant.const import (
    CONF_NAME, STATE_OK)
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_point_in_utc_time, async_track_utc_time_change)
from homeassistant.util import dt as dt_util


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'holidays'
ENTITY_ID = 'holidays.holiday'


class HolidayConfigIterator(object):
    COMMENT_RE = re.compile('(.*) *#.*')
    
    def __init__(self, path):
        self.file = open(path, 'r')

    def __next__(self):
        line = None
        while not line:
            line = self.file.readline()
            if not line:
                raise StopIteration()
            line = line.rstrip()

            m = self.COMMENT_RE.match(line)
            if m:
                line = m.group(1)

            if line:
                return line

    def __iter__(self):
        return self


def convert_date(s):
    return datetime.datetime(int(s[0:4]), int(s[4:6]), int(s[6:8]))


def setup(hass, config):
    h = Holidays(hass)
    h.point_in_time_listener(dt_util.utcnow())
    return True


class Holidays(Entity):
    entity_id = ENTITY_ID

    def __init__(self, hass):
        self.hass = hass

        if os.path.exists('/srv/homeassistant/config/holidays.csv'):
            with open('/srv/homeassistant/config/holidays.csv') as f:
                f = HolidayConfigIterator(
                    '/srv/homeassistant/config/holidays.csv')
                reader = csv.DictReader(f)

                self.holidays = {}
                for row in reader:
                    if row['Start'] and not row['End']:
                        # Single day event
                        d = convert_date(row['Start'])
                        self.holidays.setdefault(d, [])
                        self.holidays[d].append(row['Comment'])

                    else:
                        # Multiday event
                        d = convert_date(row['Start'])
                        end = convert_date(row['End'])
                        while d <= end:
                            self.holidays.setdefault(d, [])
                            self.holidays[d].append(row['Comment'])
                            d += timedelta(days=1)
        else:
            self.holidays = {}

    @property
    def name(self):
        return 'Holidays'

    @property
    def state(self):
        return STATE_OK

    @property
    def state_attributes(self):
        attrs = {}

        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)

        attrs['today'] = ', '.join(self.holidays.get(today, []))
        attrs['tomorrow'] = ', '.join(self.holidays.get(
            today + timedelta(days=1), []))
        
        return attrs

    @callback
    def point_in_time_listener(self, now):
        self.async_schedule_update_ha_state()

        async_track_point_in_utc_time(
            self.hass, self.point_in_time_listener,
            datetime.datetime.now() + timedelta(seconds=30))
