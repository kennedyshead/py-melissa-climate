#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

from requests_futures.sessions import FuturesSession
import requests
from datetime import datetime

from melissa.exceptions import ApiException

__author__ = 'Magnus Knutas'

logger = logging.getLogger(__name__)

session = FuturesSession(max_workers=10)

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


class Melissa(object):
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

    DEFAULT_DATA = {
        SERIAL_NUMBER: "",
        COMMAND: "send_ir_code",
        STATE: STATE_ON,  # 0-OFF; 1-ON; 2-Idle
        MODE: MODE_HEAT,  # 0-Auto; 1-Fan; 2-Heat; 3-Cool; 4-Dry
        TEMP: 20,  # number between 16 and 30 (depends on the codeset)
        FAN: FAN_MEDIUM  # 0-Auto; 1-Low; 2-Med; 3-High
    }

    def __init__(self, **kwargs):
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.default_headers = kwargs.get('headers', HEADERS)
        self.access_token = kwargs.get('access_token', None)
        self.refresh_token = kwargs.get('refresh_token', None)
        self.token_type = kwargs.get('token_type', None)
        self.devices = {}
        self.geofences = {}
        self._latest_humidity = None
        self._latest_temp = None
        self._latest_status = {}
        self._time_cache = kwargs.get('time_cache', CHANGE_TIME_CACHE_DEFAULT)
        self.fetch_timestamp = None
        self._send_cache = None
        if not self.have_connection():
            self._connect()

    def _connect(self):
        url = MELISSA_URL % 'auth/login'
        logger.info(url)
        data = CLIENT_DATA.copy()
        data.update(
            {'username': self.username, 'password': self.password}
        )
        logger.info(data)
        req = session.post(
            url, data=data,
            headers=HEADERS
        )
        req = req.result()
        if req.status_code == requests.codes.ok:
            resp = json.loads(req.text)
            self.access_token = resp['auth']['access_token']
            self.refresh_token = resp['auth']['refresh_token']
            self.token_type = resp['auth']['token_type']
        else:
            raise ApiException(req.text, req.status_code)

    def _get_headers(self):
        headers = self.default_headers.copy()
        headers.update(
            {'Authorization': "%s %s" % (self.token_type, self.access_token)}
        )
        logger.debug(headers)
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

    def fetch_devices(self):
        url = MELISSA_URL % 'controllers'
        logger.info(url)
        headers = self._get_headers()
        req = session.get(url, headers=headers)
        req = req.result()
        if req.status_code == requests.codes.ok:
            resp = json.loads(req.text)
            for controller in resp['_embedded']['controller']:
                self.devices[controller['serial_number']] = controller
        logger.debug(self.devices)
        return self.devices

    def fetch_geofences(self):
        url = MELISSA_URL % 'geofences'
        logger.info(url)
        headers = self._get_headers()
        req = session.get(url, headers=headers)
        req = req.result()
        if req.status_code == requests.codes.ok:
            resp = json.loads(req.text)
            for geofence in resp['_embedded']['geofence']:
                self.geofences[geofence['controller_id']] = geofence
        logger.info(self.geofences)
        return self.geofences

    def have_connection(self):
        return self.access_token

    def send(self, device, state_data=None):
        if not self._send_cache:
            data = self.DEFAULT_DATA.copy()
        else:
            data = self._send_cache
        if state_data:
            data.update(state_data)
        data.update({self.SERIAL_NUMBER: device})
        url = MELISSA_URL % 'provider/send'
        logger.info(url)
        headers = self._get_headers()
        headers.update({'Content-Type': 'application/json'})
        if self._send_cache == data:
            return True
        else:
            self.send_cache = data
        input_data = json.dumps(data)
        logger.info(input_data)
        req = session.post(url, data=input_data, headers=headers)
        req = req.result()
        if not req.status_code == requests.codes.ok:
            logger.error(req.text)
        return req.status_code == requests.codes.ok

    def status(self, test=False, cached=False):
        if cached and self.fetch_timestamp and self._time_cache > \
                (datetime.utcnow() - self.fetch_timestamp).total_seconds():
            return self._latest_status
        url = MELISSA_URL % 'provider/fetch'
        logger.info(url)
        headers = self._get_headers()
        headers.update({'Content-Type': 'application/json'})
        ret = {}
        if not self.devices:
            self.fetch_devices()
        for device in self.devices:
            input_data = json.dumps({'serial_number': device})
            req = session.post(
                url, data=input_data, headers=headers)
            req = req.result()
            if req.status_code == requests.codes.ok:
                data = json.loads(req.text)
                if self.sanity_check(data['provider'], device):
                    ret[device] = data['provider']
                else:
                    ret[device] = self._latest_status[device]
            elif req.status_code == requests.codes.unauthorized and not test:
                self._connect()
                return self.status(test=True)
            else:
                raise ApiException(req.text)
        self.fetch_timestamp = datetime.utcnow()
        self._latest_status = ret
        return ret

    def cur_settings(self, serial_number):
        url = MELISSA_URL % 'controllers/%s' % serial_number
        logger.info(url)
        headers = self._get_headers()
        req = session.get(
                url, headers=headers)
        req = req.result()
        if req.status_code == requests.codes.ok:
            data = json.loads(req.text)
        else:
            raise ApiException(req.text)
        logger.debug(data)
        return data
