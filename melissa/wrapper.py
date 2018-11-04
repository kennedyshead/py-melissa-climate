#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

import requests
from requests_futures.sessions import FuturesSession
from datetime import datetime

from melissa.core import CoreMelissa, CHANGE_TIME_CACHE_DEFAULT, HEADERS, \
    MELISSA_URL, CLIENT_DATA
from melissa.exceptions import ApiException

__author__ = 'Magnus Knutas'
LOGGER = logging.getLogger(__name__)

SESSION = FuturesSession(max_workers=10)


class Melissa(CoreMelissa):

    def __init__(self, **kwargs):
        super(Melissa, self).__init__(**kwargs)
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.refresh_token = kwargs.get('refresh_token', None)
        self.devices = {}
        self.geofences = {}
        self._latest_humidity = None
        self._latest_temp = None
        self._time_cache = kwargs.get('time_cache', CHANGE_TIME_CACHE_DEFAULT)
        self.fetch_timestamp = None
        self._send_cache = None
        if not self.have_connection:
            self._connect()

    def _connect(self):
        url = MELISSA_URL % 'auth/login'
        LOGGER.info(url)
        data = CLIENT_DATA.copy()
        data.update(
            {'username': self.username, 'password': self.password}
        )
        LOGGER.info(data)
        req = SESSION.post(
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

    def fetch_devices(self):
        url = MELISSA_URL % 'controllers'
        LOGGER.info(url)
        headers = self._get_headers()
        req = SESSION.get(url, headers=headers)
        req = req.result()
        if req.status_code == requests.codes.ok:
            resp = json.loads(req.text)
            for controller in resp['_embedded']['controller']:
                self.devices[controller['serial_number']] = controller
        LOGGER.debug(self.devices)
        return self.devices

    def fetch_geofences(self):
        url = MELISSA_URL % 'geofences'
        LOGGER.info(url)
        headers = self._get_headers()
        req = SESSION.get(url, headers=headers)
        req = req.result()
        if req.status_code == requests.codes.ok:
            resp = json.loads(req.text)
            for geofence in resp['_embedded']['geofence']:
                self.geofences[geofence['controller_id']] = geofence
        LOGGER.info(self.geofences)
        return self.geofences

    def send(self, device, device_type='melissa', state_data=None):
        if not self._send_cache:
            if device_type == 'melissa':
                data = self.DEFAULT_DATA_MELISSA.copy()
            if device_type == 'bobbie':
                data = self.DEFAULT_DATA_BOBBIE.copy()
        else:
            data = self._send_cache.copy()
        if state_data:
            data.update(state_data)
        data.update({self.SERIAL_NUMBER: device})
        url = MELISSA_URL % 'provider/send'
        LOGGER.info(url)
        headers = self._get_headers()
        headers.update({'Content-Type': 'application/json'})
        if self._send_cache == data:
            return True
        else:
            self._send_cache = data
        input_data = json.dumps(data)
        LOGGER.info(input_data)
        req = SESSION.post(url, data=input_data, headers=headers)
        req = req.result()
        if not req.status_code == requests.codes.ok:
            return False
        return req.status_code == requests.codes.ok

    def status(self, test=False, cached=False):
        # TODO: Update self._send_cache
        if cached and self.fetch_timestamp and self._time_cache > \
                (datetime.utcnow() - self.fetch_timestamp).total_seconds():
            return self._latest_status
        url = MELISSA_URL % 'provider/fetch'
        LOGGER.info(url)
        headers = self._get_headers()
        headers.update({'Content-Type': 'application/json'})
        ret = {}
        if not self.devices:
            self.fetch_devices()
        for device in self.devices:
            if self.devices[device]['type'] in ('melissa', 'bobbie'):
                input_data = json.dumps({'serial_number': device})
                req = SESSION.post(
                    url, data=input_data, headers=headers)
                req = req.result()
                if req.status_code == requests.codes.ok:
                    data = json.loads(req.text)
                    if self.devices[device]['type'] == 'bobbie':
                        ret[device] = data['provider']
                    elif self.sanity_check(data['provider'], device):
                        ret[device] = data['provider']
                    else:
                        ret[device] = self._latest_status[device]
                elif req.status_code == requests.codes.unauthorized and \
                        not test:
                    self._connect()
                    return self.status(test=True)
                else:
                    raise ApiException(req.text)
        self.fetch_timestamp = datetime.utcnow()
        self._latest_status = ret
        return ret

    def cur_settings(self, serial_number):
        url = MELISSA_URL % 'controllers/%s' % serial_number
        LOGGER.info(url)
        headers = self._get_headers()
        req = SESSION.get(
                url, headers=headers)
        req = req.result()
        if req.status_code == requests.codes.ok:
            data = json.loads(req.text)
        else:
            raise ApiException(req.text)
        LOGGER.debug(data)
        return data
