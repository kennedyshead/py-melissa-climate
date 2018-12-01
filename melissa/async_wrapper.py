#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Async version of the wrapper.
"""
import json
import logging
from datetime import datetime

import aiohttp
import requests
from melissa.exceptions import ApiException, UnsupportedDevice

from melissa import CHANGE_TIME_CACHE_DEFAULT, HEADERS, MELISSA_URL, \
    CLIENT_DATA
from melissa.core import CoreMelissa

__author__ = 'Magnus Knutas'
LOGGER = logging.getLogger(__name__)


class AsyncMelissa(CoreMelissa):
    """
    Async class for Melissa.
    """
    session = None

    def __init__(self, **kwargs):
        super(AsyncMelissa, self).__init__(**kwargs)
        self.session = aiohttp.ClientSession(connector_owner=False)
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.refresh_token = kwargs.get('refresh_token', None)
        self.devices = {}
        self.geofences = {}
        self._latest_humidity = None
        self._latest_temp = None
        self._latest_status = {}
        self._time_cache = kwargs.get('time_cache', CHANGE_TIME_CACHE_DEFAULT)
        self.fetch_timestamp = None

    async def async_connect(self):
        url = MELISSA_URL % 'auth/login'
        LOGGER.info(url)
        data = CLIENT_DATA.copy()
        data.update(
            {'username': self.username, 'password': self.password}
        )
        LOGGER.info(data)
        req = await self.session.post(
            url, data=data,
            headers=HEADERS
        )
        if req.status == requests.codes.ok:
            resp = json.loads(await req.text())
            self.access_token = resp['auth']['access_token']
            self.refresh_token = resp['auth']['refresh_token']
            self.token_type = resp['auth']['token_type']
        else:
            raise ApiException(await req.text(), req.status)

    async def async_fetch(self, url):
        response = await self.session.get(url)
        ret = await response.text()
        return ret

    async def async_fetch_devices(self):
        url = MELISSA_URL % 'controllers'
        LOGGER.info(url)
        headers = self._get_headers()
        req = await self.session.get(url, headers=headers)
        if req.status == requests.codes.ok:
            resp = json.loads(await req.text())
            for controller in resp['_embedded']['controller']:
                self.devices[controller['serial_number']] = controller
        LOGGER.debug(self.devices)
        return self.devices

    async def async_fetch_geofences(self):
        url = MELISSA_URL % 'geofences'
        LOGGER.info(url)
        headers = self._get_headers()
        req = await self.session.get(url, headers=headers)
        if req.status == requests.codes.ok:
            resp = json.loads(await req.text())
            for geofence in resp['_embedded']['geofence']:
                self.geofences[geofence['controller_id']] = geofence
        LOGGER.info(self.geofences)
        return self.geofences

    async def async_send(self, device, device_type='melissa', state_data=None):
        if device_type == 'melissa':
            data = self.DEFAULT_DATA_MELISSA.copy()
        elif device_type == 'bobbie':
            data = self.DEFAULT_DATA_BOBBIE.copy()
        else:
            raise UnsupportedDevice(device_type)

        if state_data:
            data.update(state_data)

        data.update({self.SERIAL_NUMBER: device})
        url = MELISSA_URL % 'provider/send'
        LOGGER.info(url)

        if not self.have_connection:
            await self.async_connect()

        headers = self._get_headers()
        headers.update({'Content-Type': 'application/json'})

        input_data = json.dumps(data)
        LOGGER.debug(input_data)
        req = await self.session.post(url, data=input_data, headers=headers)
        if not req.status == requests.codes.ok:
            raise ApiException("%s - %s", (req.status, req.text()))

        return True

    async def async_status(self, test=False, cached=False):
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
            await self.async_fetch_devices()
        for device in self.devices:
            if self.devices[device]['type'] in ('melissa', 'bobbie'):
                input_data = json.dumps({'serial_number': device})
                req = await self.session.post(
                    url, data=input_data, headers=headers)
                if req.status == requests.codes.ok:
                    data = json.loads(await req.text())
                    if self.devices[device]['type'] == 'bobbie':
                        ret[device] = data['provider']
                    elif self.sanity_check(data['provider'], device):
                        ret[device] = data['provider']
                    else:
                        ret[device] = self._latest_status[device]
                elif req.status == requests.codes.unauthorized and \
                        not test:
                    await self.async_connect()
                    return self.async_status()
                else:
                    raise ApiException(await req.text())
        self.fetch_timestamp = datetime.utcnow()
        self._latest_status = ret
        return ret

    async def async_cur_settings(self, serial_number):
        url = MELISSA_URL % 'controllers/%s' % serial_number
        LOGGER.info(url)
        headers = self._get_headers()
        req = await self.session.get(
                url, headers=headers)
        if req.status == requests.codes.ok:
            data = json.loads(await req.text())
        else:
            raise ApiException(await req.text())
        LOGGER.debug(data)
        return data
