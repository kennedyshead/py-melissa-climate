#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from unittest import TestCase, mock

from melissa import ApiException
from melissa.wrapper import MELISSA_URL, Melissa
from tests.helpers import load_fixture

__author__ = 'Magnus Knutas'

AUTH_LOGIN_URL = MELISSA_URL % 'auth/login'
STATUS_URL = MELISSA_URL % 'provider/fetch'
FETCH_DEVICES_URL = MELISSA_URL % 'controllers'
FETCH_GEOFENCES_URL = MELISSA_URL % 'geofences'
SEND_URL = MELISSA_URL % 'provider/send'
CUR_SETTINGS_URL = MELISSA_URL % 'controllers/12345678'

LOGGED_IN_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,sv-SE;q=0.9',
    'Authorization': 'Bearer 12345678',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 7.0; SM-G935F Build/NRD90M; wv)'
                  ' AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                  'Chrome/63.0.3239.111 Mobile Safari/537.36',
    'X-Requested-With': 'at.cloudfaces.melissa'
}

FETCH_DEVICES_DATA_OK = {
    '12345678': {
        '_links': {'self': {'href': '/v1/controllers'}},
        'brand_id': 1,
        'controller_log': {
            'created': '2018-01-16T18:02:36.735Z',
            'humidity': 15.3,
            'raw_humidity': 11142,
            'raw_temperature': 29384,
            'temp': 28.6},
        'created': '2016-07-06 18:59:46',
        'firmware_version': 'V1SHTHF',
        'id': 1,
        'mac': '12345678',
        'name': 'Melissa 12345678',
        'online': True,
        'room_id': None,
        'serial_number': '12345678',
        'type': 'melissa',
        'user_id': 1}
}

FETCH_GEOFENCES_DATA_OK = {
    '12345678': {
        '_links': {'self': {'href': '/v1/geofences/1'}},
        'active': 1,
        'controller_id': '12345678',
        'enter_command_fields': '{"state":1,"mode":"2","temp":30,"fan":"3"}',
        'enter_command_name': 'send_ir_code',
        'enter_push': 1,
        'exit_command_fields': '{"state":0,"mode":3,"temp":25,"fan":0}',
        'exit_command_name': 'send_ir_code',
        'exit_push': 1,
        'id': 1,
        'latitude': 1,
        'longitude': 1,
        'radius': 1500,
        'user_id': 1}
}

CUR_SETTINGS_DATA_OK = {
    '_links': {'self': {'href': '/v1/controllers/12345678'}},
    'controller': {
        '_relation': {
            'command_log': {
                'fan': 2,
                'mode': 2,
                'state': 1,
                'temp': 16
            }
        },
        'created': '2016-07-06 18:59:46',
        'deleted_at': None,
        'firmware_version': 'V1SHTHF',
        'id': 1,
        'mac': '12345678',
        'name': 'Melissa 12345678',
        'online': False,
        'room_id': None,
        'serial_number': '12345678',
        'type': 'melissa',
        'user_id': 1
    }
}


class MockResponse:
    def __init__(self, text, status_code):
        self._text = text
        self.status_code = status_code

    @property
    def text(self):
        return self._text

    def result(self):
        return self


# This method will be used by the mock to replace requests.get
def mocked_requests_post(*args, **kwargs):
    if args[0] == AUTH_LOGIN_URL:
        return MockResponse(load_fixture('auth_login.json'), 200)
    elif args[0] == STATUS_URL:
        return MockResponse(load_fixture('status.json'), 200)
    elif args[0] == SEND_URL:
        return MockResponse(load_fixture('send.json'), 200)

    return MockResponse(None, 404)


# This method will be used by the mock to replace requests.get
def mocked_requests_post_bad(*args, **kwargs):
    if args[0] == AUTH_LOGIN_URL:
        return MockResponse(load_fixture('auth_login_denied.json'), 401)
    elif args[0] == SEND_URL:
        return MockResponse(load_fixture('error.json'), 500)
    elif args[0] == STATUS_URL:
        return MockResponse(load_fixture('bad_temp_status.json'), 200)

    return MockResponse(None, 404)


def mocked_requests_get(*args, **kwargs):
    if args[0] == FETCH_DEVICES_URL:
        return MockResponse(load_fixture('fetch_devices.json'), 200)
    elif args[0] == FETCH_GEOFENCES_URL:
        return MockResponse(load_fixture('fetch_geofences.json'), 200)
    elif args[0] == CUR_SETTINGS_URL:
        return MockResponse(load_fixture('cur_settings.json'), 200)

    return MockResponse(None, 404)


class TestMelissa(TestCase):

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_init(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertEqual(melissa.access_token, '12345678')
        self.assertEqual(melissa.refresh_token, '12345678')
        self.assertEqual(melissa.username, '1234')
        self.assertEqual(melissa.password, '4321')

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_connect_ok(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertIsNone(melissa._connect())

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post_bad)
    def test_connect_bad(self, mock_post):
        self.assertRaises(ApiException, Melissa,
                          username="1234", password="4321")

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_get_headers(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertEqual(melissa._get_headers(), LOGGED_IN_HEADERS)

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_sanity_check(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        melissa._latest_temp = 28.9
        melissa._latest_status['12345678'] = json.loads(
            load_fixture('status.json'))['provider']
        data = json.loads(load_fixture('bad_temp_status.json'))['provider']
        device = '12345678'
        self.assertFalse(melissa.sanity_check(data, device))
        data = json.loads(load_fixture('bad_hum_status.json'))['provider']
        self.assertFalse(melissa.sanity_check(data, device))

    @mock.patch('melissa.wrapper.SESSION.get',
                side_effect=mocked_requests_get)
    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_fetch_devices(self, mock_get, mock_post):
        melissa = Melissa(username="1234", password="4321")
        resp = melissa.fetch_devices()
        self.assertEqual(resp, FETCH_DEVICES_DATA_OK)

    @mock.patch('melissa.wrapper.SESSION.get',
                side_effect=mocked_requests_get)
    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_fetch_geofences(self, mock_get, mock_post):
        melissa = Melissa(username="1234", password="4321")
        resp = melissa.fetch_geofences()
        self.assertEqual(resp, FETCH_GEOFENCES_DATA_OK)

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_have_connection(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertTrue(melissa.have_connection())
        melissa.access_token = None
        self.assertFalse(melissa.have_connection())

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_send_ok(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertTrue(melissa.send('12345678', {'temp': 20}))

    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    @mock.patch('melissa.wrapper.LOGGER')
    def test_send(self, mock_post, mock_logger):
        melissa = Melissa(username="1234", password="4321")
        self.assertTrue(melissa.send('12345678', {'temp': 20}))
        with mock.patch('melissa.wrapper.SESSION.post',
                        side_effect=mocked_requests_post_bad) as mock_post:
            melissa._send_cache = None
            self.assertFalse(melissa.send('12345678', {'temp': 21}))

    @mock.patch('melissa.wrapper.SESSION.get',
                side_effect=mocked_requests_get)
    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_status(self, mocked_get, mocked_post):
        melissa = Melissa(username="1234", password="4321")
        good_status = melissa.status()
        with mock.patch('melissa.wrapper.SESSION.post',
                        side_effect=mocked_requests_post_bad) as mock_post:
            melissa.fetch_timestamp = None
            bad_status = melissa.status()
        self.assertEqual(good_status, bad_status)

    @mock.patch('melissa.wrapper.SESSION.get',
                side_effect=mocked_requests_get)
    @mock.patch('melissa.wrapper.SESSION.post',
                side_effect=mocked_requests_post)
    def test_cur_settings(self, mocked_get, mocked_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertEqual(melissa.cur_settings(
            '12345678'), CUR_SETTINGS_DATA_OK)
