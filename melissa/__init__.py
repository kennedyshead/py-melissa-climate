#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import requests

from melissa.exceptions import ApiException

__author__ = 'Magnus Knutas'

logger = logging.getLogger(__name__)

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


class Melissa(object):
    def __init__(self, **kwargs):
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.access_token = kwargs.get('access_token', None)
        self.refresh_token = kwargs.get('refresh_token', None)
        self.token_type = kwargs.get('token_type', None)
        self.devices = {}
        self.geofences = {}
        if not self.have_connection():
            self._connect()

    def _connect(self):
        url = MELISSA_URL % 'auth/login'
        logger.info(url)
        data = CLIENT_DATA
        data.update(
            {'username': self.username, 'password': self.password}
        )
        logger.debug(data)
        req = requests.post(
            url, data=data,
            headers=HEADERS
        )
        if req.status_code == requests.codes.ok:
            resp = json.loads(req.text)
            self.access_token = resp['auth']['access_token']
            self.refresh_token = resp['auth']['refresh_token']
            self.token_type = resp['auth']['token_type']
            self.fetch_devices()
        else:
            raise ApiException(req.text)

    def _get_headers(self):
        headers = HEADERS
        headers.update(
            {'Authorization': "%s %s" % (self.token_type, self.access_token)}
        )
        logger.debug(headers)
        return headers

    def fetch_devices(self):
        url = MELISSA_URL % 'controllers'
        logger.info(url)
        headers = self._get_headers()
        req = requests.get(url, headers=headers)
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
        req = requests.get(url, headers=headers)
        if req.status_code == requests.codes.ok:
            resp = json.loads(req.text)
            for geofence in resp['_embedded']['geofence']:
                self.geofences[geofence['controller_id']] = geofence
        logger.debug(self.devices)
        return self.devices

    def have_connection(self):
        return self.access_token

    def status(self):
        url = MELISSA_URL % 'provider/fetch'
        logger.info(url)
        headers = self._get_headers()
        ret = {}
        for device in self.devices.keys():
            input_data = json.dumps({'serial_number': device})
            print(input_data)
            headers.update({'Content-Type': 'application/json'})
            print(headers)
            req = requests.post(
                url, data=input_data, headers=headers)
            if req.status_code == requests.codes.ok:
                data = json.loads(req.text)
                ret[device] = data['provider']
            else:
                raise ApiException(req.text)
        logger.debug(ret)
        return ret
