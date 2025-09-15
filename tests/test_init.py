import json
import pytest
from unittest import TestCase, mock

from melissa import ApiException, MELISSA_URL, AsyncMelissa as Melissa
from tests.helpers import load_fixture

AUTH_LOGIN_URL = MELISSA_URL % "auth/login"
STATUS_URL = MELISSA_URL % "provider/fetch"
FETCH_DEVICES_URL = MELISSA_URL % "controllers"
FETCH_GEOFENCES_URL = MELISSA_URL % "geofences"
SEND_URL = MELISSA_URL % "provider/send"
CUR_SETTINGS_URL = MELISSA_URL % "controllers/12345678"

LOGGED_IN_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,sv-SE;q=0.9",
    "Authorization": "Bearer 12345678",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.0; SM-G935F Build/NRD90M; wv)"
    " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Chrome/63.0.3239.111 Mobile Safari/537.36",
    "X-Requested-With": "at.cloudfaces.melissa",
}

FETCH_DEVICES_DATA_OK = {
    "12345678": {
        "_links": {"self": {"href": "/v1/controllers"}},
        "brand_id": 1,
        "controller_log": {
            "created": "2018-01-16T18:02:36.735Z",
            "humidity": 15.3,
            "raw_humidity": 11142,
            "raw_temperature": 29384,
            "temp": 28.6,
        },
        "created": "2016-07-06 18:59:46",
        "firmware_version": "V1SHTHF",
        "id": 1,
        "mac": "12345678",
        "name": "Melissa 12345678",
        "online": True,
        "room_id": None,
        "serial_number": "12345678",
        "type": "melissa",
        "user_id": 1,
    }
}

FETCH_GEOFENCES_DATA_OK = {
    "12345678": {
        "_links": {"self": {"href": "/v1/geofences/1"}},
        "active": 1,
        "controller_id": "12345678",
        "enter_command_fields": '{"state":1,"mode":"2","temp":30,"fan":"3"}',
        "enter_command_name": "send_ir_code",
        "enter_push": 1,
        "exit_command_fields": '{"state":0,"mode":3,"temp":25,"fan":0}',
        "exit_command_name": "send_ir_code",
        "exit_push": 1,
        "id": 1,
        "latitude": 1,
        "longitude": 1,
        "radius": 1500,
        "user_id": 1,
    }
}

CUR_SETTINGS_DATA_OK = {
    "_links": {"self": {"href": "/v1/controllers/12345678"}},
    "controller": {
        "_relation": {
            "command_log": {"fan": 2, "mode": 2, "state": 1, "temp": 16}
        },
        "created": "2016-07-06 18:59:46",
        "deleted_at": None,
        "firmware_version": "V1SHTHF",
        "id": 1,
        "mac": "12345678",
        "name": "Melissa 12345678",
        "online": False,
        "room_id": None,
        "serial_number": "12345678",
        "type": "melissa",
        "user_id": 1,
    },
}


class MockResponse:
    def __init__(self, text: str, status_code: int) -> None:
        self._text = text
        self.status_code = status_code

    @property
    def text(self) -> str:
        return self._text

    def result(self) -> "MockResponse":
        return self


# This method will be used by the mock to replace requests.get
def mocked_post(*args, **kwargs):
    if args[0] == AUTH_LOGIN_URL:
        return MockResponse(load_fixture("auth_login.json"), 200)
    elif args[0] == STATUS_URL:
        return MockResponse(load_fixture("status.json"), 200)
    elif args[0] == SEND_URL:
        return MockResponse(load_fixture("send.json"), 200)

    return MockResponse(None, 404)


# This method will be used by the mock to replace requests.get
def mocked_post_bad(*args, **kwargs):
    if args[0] == AUTH_LOGIN_URL:
        return MockResponse(load_fixture("auth_login_denied.json"), 401)
    elif args[0] == SEND_URL:
        return MockResponse(load_fixture("error.json"), 500)
    elif args[0] == STATUS_URL:
        return MockResponse(load_fixture("bad_temp_status.json"), 200)

    return MockResponse(None, 404)


def mocked_get(*args, **kwargs):
    if args[0] == FETCH_DEVICES_URL:
        return MockResponse(load_fixture("fetch_devices.json"), 200)
    elif args[0] == FETCH_GEOFENCES_URL:
        return MockResponse(load_fixture("fetch_geofences.json"), 200)
    elif args[0] == CUR_SETTINGS_URL:
        return MockResponse(load_fixture("cur_settings.json"), 200)

    return MockResponse(None, 404)


class TestMelissa(TestCase):
    @mock.patch("melissa.ClientSession")
    def test_init(self, mock_post):
        melissa = Melissa(
            username="1234",
            password="4321",
            access_token="12345678",
            refresh_token="12345678",
        )
        self.assertEqual(melissa.username, "1234")
        self.assertEqual(melissa.password, "4321")
        self.assertEqual(melissa.access_token, "12345678")
        self.assertEqual(melissa.refresh_token, "12345678")

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    async def test_connect_ok(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertIsNone(await melissa.async_connect())

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    async def test_connect_bad(self, mock_post):
        mock_post.post.side_effect = mocked_post_bad
        melissa = Melissa(username="1234", password="4321")
        self.assertRaises(ApiException, await melissa.async_connect())

    @mock.patch("melissa.ClientSession")
    def test_get_headers(self, mock_post):
        melissa = Melissa(
            username="1234",
            password="4321",
            access_token="12345678",
            token_type="Bearer",
        )
        assert melissa._get_headers() == LOGGED_IN_HEADERS

    @mock.patch("melissa.ClientSession")
    def test_sanity_check(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        melissa._latest_temp = 28.9
        melissa._latest_status["12345678"] = json.loads(
            load_fixture("status.json")
        )["provider"]
        data = json.loads(load_fixture("bad_temp_status.json"))["provider"]
        device = "12345678"
        self.assertFalse(melissa.sanity_check(data, device))
        data = json.loads(load_fixture("bad_hum_status.json"))["provider"]
        self.assertFalse(melissa.sanity_check(data, device))

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    @mock.patch("melissa.ClientSession")
    async def test_fetch_devices(self, mock_get, mock_post):
        melissa = Melissa(username="1234", password="4321")
        resp = await melissa.async_fetch_devices()
        self.assertEqual(resp, FETCH_DEVICES_DATA_OK)

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    @mock.patch("melissa.ClientSession")
    async def test_fetch_geofences(self, mock_get, mock_post):
        melissa = Melissa(username="1234", password="4321")
        resp = await melissa.async_fetch_geofences()
        self.assertEqual(resp, FETCH_GEOFENCES_DATA_OK)

    @mock.patch("melissa.ClientSession")
    def test_have_connection(self, mock_post):
        melissa = Melissa(
            username="1234", password="4321", access_token="12345678"
        )
        self.assertTrue(melissa.have_connection)
        melissa.access_token = None
        self.assertFalse(melissa.have_connection)

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    async def test_send_ok(self, mock_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertTrue(
            await melissa.async_send("12345678", "melissa", {"temp": 20})
        )

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    @mock.patch("melissa.LOGGER")
    async def test_send(self, mock_post, mock_logger):
        melissa = Melissa(username="1234", password="4321")
        self.assertTrue(
            await melissa.async_send("12345678", "melissa", {"temp": 20})
        )
        with mock.patch(
            "melissa.ClientSession.post",
            side_effect=mocked_post_bad,
        ):
            self.assertFalse(
                await melissa.async_send("12345678", "melissa", {"temp": 21})
            )

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    async def test_status(self, mocked_get, mocked_post):
        melissa = Melissa(username="1234", password="4321")
        good_status = await melissa.async_status()
        with mock.patch(
            "melissa.ClientSession.post",
            side_effect=mocked_post_bad,
        ):
            melissa.fetch_timestamp = None
            bad_status = await melissa.async_status()
        self.assertEqual(good_status, bad_status)

    @pytest.mark.asyncio
    @mock.patch("melissa.ClientSession")
    async def test_cur_settings(self, mocked_get, mocked_post):
        melissa = Melissa(username="1234", password="4321")
        self.assertEqual(
            await melissa.async_cur_settings("12345678"), CUR_SETTINGS_DATA_OK
        )
