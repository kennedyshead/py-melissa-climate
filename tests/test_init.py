import json
from typing import Any, Dict, Optional

from _pytest.monkeypatch import MonkeyPatch
from pytest import fixture, mark, raises

from melissa import MELISSA_URL, ApiException
from melissa import AsyncMelissa as Melissa
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

FETCH_DEVICES_DATA_OK: Dict[str, Dict[str, Any]] = {
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

FETCH_GEOFENCES_DATA_OK: Dict[str, Dict[str, Any]] = {
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
    def __init__(self, text: Optional[str], status_code: int) -> None:
        self._text = text
        self.status = status_code

    async def text(self) -> Optional[str]:
        return self._text

    def result(self) -> "MockResponse":
        return self


class MockedClientSession:
    def __init__(*args: Any, **kwargs: Any) -> None:
        """Dummy init method"""

    async def post(self, *args: Any, **kwargs: Any) -> MockResponse:
        if args[0] == AUTH_LOGIN_URL:
            return MockResponse(load_fixture("auth_login.json"), 200)
        elif args[0] == STATUS_URL:
            return MockResponse(load_fixture("status.json"), 200)
        elif args[0] == SEND_URL:
            return MockResponse(load_fixture("send.json"), 200)

        return MockResponse(None, 404)

    async def get(self, *args: Any, **kwargs: Any) -> MockResponse:
        print(args)
        if args[0] == FETCH_DEVICES_URL:
            return MockResponse(load_fixture("fetch_devices.json"), 200)
        elif args[0] == FETCH_GEOFENCES_URL:
            return MockResponse(load_fixture("fetch_geofences.json"), 200)
        elif args[0] == CUR_SETTINGS_URL:
            return MockResponse(load_fixture("cur_settings.json"), 200)

        return MockResponse(None, 404)


@fixture(autouse=True)
def mocked_aiohttp(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("melissa.ClientSession", MockedClientSession)


async def mocked_post_bad(*args: Any, **kwargs: Any) -> MockResponse:
    if args[0] == AUTH_LOGIN_URL:
        return MockResponse(load_fixture("auth_login_denied.json"), 401)
    elif args[0] == SEND_URL:
        return MockResponse(load_fixture("error.json"), 500)
    elif args[0] == STATUS_URL:
        return MockResponse(load_fixture("bad_temp_status.json"), 200)

    return MockResponse(None, 404)


def test_init() -> None:
    melissa = Melissa(
        username="1234",
        password="4321",
        access_token="12345678",
        refresh_token="12345678",
    )
    assert melissa.username == "1234"
    assert melissa.password == "4321"
    assert melissa.access_token == "12345678"
    assert melissa.refresh_token == "12345678"


@mark.asyncio
async def test_connect_bad(monkeypatch: MonkeyPatch) -> None:
    melissa = Melissa(username="1234", password="4321")
    monkeypatch.setattr("melissa.ClientSession.post", mocked_post_bad)
    with raises(ApiException):
        await melissa.async_connect()


def test_get_headers() -> None:
    melissa = Melissa(
        username="1234",
        password="4321",
        access_token="12345678",
        token_type="Bearer",
    )
    assert melissa._get_headers() == LOGGED_IN_HEADERS


def test_sanity_check() -> None:
    melissa = Melissa(username="1234", password="4321")
    melissa._latest_temp = 28.9
    melissa._latest_status["12345678"] = json.loads(
        load_fixture("status.json")
    )["provider"]
    data = json.loads(load_fixture("bad_temp_status.json"))["provider"]
    device = "12345678"
    assert not melissa.sanity_check(data, device)
    data = json.loads(load_fixture("bad_hum_status.json"))["provider"]
    assert not melissa.sanity_check(data, device)


@mark.asyncio
async def test_fetch_devices() -> None:
    melissa = Melissa(username="1234", password="4321")
    resp = await melissa.async_fetch_devices()
    assert resp == FETCH_DEVICES_DATA_OK


@mark.asyncio
async def test_fetch_geofences() -> None:
    melissa = Melissa(username="1234", password="4321")
    resp = await melissa.async_fetch_geofences()
    assert resp == FETCH_GEOFENCES_DATA_OK


def test_have_connection() -> None:
    melissa = Melissa(
        username="1234", password="4321", access_token="12345678"
    )
    assert melissa.have_connection
    melissa.access_token = None
    assert not melissa.have_connection


@mark.asyncio
async def test_send_ok() -> None:
    melissa = Melissa(username="1234", password="4321")
    assert await melissa.async_send("12345678", "melissa", {"temp": 20})


@mark.asyncio
async def test_send() -> None:
    melissa = Melissa(username="1234", password="4321")
    assert await melissa.async_send("12345678", "melissa", {"temp": 20})


@mark.asyncio
async def test_status() -> None:
    melissa = Melissa(username="1234", password="4321")
    good_status = await melissa.async_status()
    melissa.fetch_timestamp = None
    bad_status = await melissa.async_status()
    assert good_status == bad_status


@mark.asyncio
async def test_cur_settings() -> None:
    melissa = Melissa(username="1234", password="4321")
    assert await melissa.async_cur_settings("12345678") == CUR_SETTINGS_DATA_OK
