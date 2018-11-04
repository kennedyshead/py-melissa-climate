#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core things for Melissa platform.
"""
import logging

MELISSA_URL = 'http://developer-api.seemelissa.com/v1/%s'
CLIENT_DATA = {
    'client_id': 'mclimate',
    'client_secret': 'mclimate_core'
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 7.0; SM-G935F Build/NRD90M; wv)'
                  ' AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0'
                  ' Chrome/63.0.3239.111 Mobile Safari/537.36',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,sv-SE;q=0.9',
    'X-Requested-With': 'at.cloudfaces.melissa'
}

CHANGE_THRESHOLD = 10
MIN_HUMIDITY_ALLOWED = 10
CHANGE_TIME_CACHE_DEFAULT = 120  # 2 min default

_LOGGER = logging.getLogger(__name__)


class CoreMelissa:
    """
    Core class for Melissa
    """
    SERIAL_NUMBER = 'serial_number'
    COMMAND = 'command'
    STATE = 'state'
    MODE = 'mode'
    TEMP = 'temp'
    FAN = 'fan'
    HUMIDITY = 'humidity'

    FAN_AUTO = 0
    FAN_LOW = 1
    FAN_MEDIUM = 2
    FAN_HIGH = 3

    STATE_OFF = 0
    STATE_ON = 1
    STATE_IDLE = 2

    MODE_AUTO = 0
    MODE_FAN = 1
    MODE_HEAT = 2
    MODE_COOL = 3
    MODE_DRY = 4

    DEFAULT_DATA_MELISSA = {
        SERIAL_NUMBER: "",
        COMMAND: "send_ir_code",
        STATE: STATE_ON,  # 0-OFF; 1-ON; 2-Idle
        MODE: MODE_HEAT,  # 0-Auto; 1-Fan; 2-Heat; 3-Cool; 4-Dry
        TEMP: 20,  # number between 16 and 30 (depends on the codeset)
        FAN: FAN_MEDIUM  # 0-Auto; 1-Low; 2-Med; 3-High
    }

    DEFAULT_DATA_BOBBIE = {
        SERIAL_NUMBER: "",
        COMMAND: "switch_on_off",
        STATE: 'on'
    }

    def __init__(self, **kwargs):
        self.default_headers = kwargs.get('headers', HEADERS)
        self.access_token = kwargs.get('access_token', None)
        self.token_type = kwargs.get('token_type', None)
        self._latest_status = {}

    def _get_headers(self):
        headers = self.default_headers.copy()
        headers.update(
            {'Authorization': "%s %s" % (self.token_type, self.access_token)}
        )
        _LOGGER.debug(headers)
        return headers

    def sanity_check(self, data, device):
        ret = True
        if self._latest_status and self._latest_status.get(device) and abs(
                data[self.TEMP] - self._latest_status[device][self.TEMP]
        ) > CHANGE_THRESHOLD:
            ret = False
        if self._latest_status and self._latest_status.get(device) and \
                data[self.HUMIDITY] < MIN_HUMIDITY_ALLOWED:
            ret = False
        return ret

    @property
    def have_connection(self):
        return self.access_token is not None
