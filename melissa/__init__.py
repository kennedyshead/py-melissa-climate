"""Python implementation of the mclimate api."""

import json
import logging
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from numbers import Number
from typing import Any, Dict, Optional, Union

from aiohttp import ClientSession

from .const import (
    CHANGE_THRESHOLD,
    CHANGE_TIME_CACHE_DEFAULT,
    CLIENT_DATA,
    HEADERS,
    MELISSA_URL,
    MIN_HUMIDITY_ALLOWED,
)
from .exceptions import ApiException, UnsupportedDevice

try:
    __version__ = version("melissa")
except PackageNotFoundError:
    __version__ = "dev"

__author__ = "Magnus Knutas"

_LOGGER = logging.getLogger(__name__)

__all__ = ("ApiException", "AsyncMelissa", "MELISSA_URL")


class AsyncMelissa:
    """Async class for Melissa."""

    SERIAL_NUMBER: str = "serial_number"
    COMMAND: str = "command"
    STATE: str = "state"
    MODE: str = "mode"
    TEMP: str = "temp"
    FAN: str = "fan"
    HUMIDITY: str = "humidity"

    FAN_AUTO: int = 0
    FAN_LOW: int = 1
    FAN_MEDIUM: int = 2
    FAN_HIGH: int = 3

    STATE_OFF: int = 0
    STATE_ON: int = 1
    STATE_IDLE: int = 2

    MODE_AUTO: int = 0
    MODE_FAN: int = 1
    MODE_HEAT: int = 2
    MODE_COOL: int = 3
    MODE_DRY: int = 4

    LED_ON: str = "reset_color"
    LED_OFF: str = "turn_led_off"

    DEFAULT_DATA_MELISSA: Dict[str, Union[int, str]] = {
        SERIAL_NUMBER: "",
        COMMAND: "send_ir_code",
        STATE: STATE_ON,  # 0-OFF; 1-ON; 2-Idle
        MODE: MODE_HEAT,  # 0-Auto; 1-Fan; 2-Heat; 3-Cool; 4-Dry
        TEMP: 20,  # number between 16 and 30 (depends on the codeset)
        FAN: FAN_MEDIUM,  # 0-Auto; 1-Low; 2-Med; 3-High
    }

    DEFAULT_DATA_BOBBIE: Dict[str, str] = {
        SERIAL_NUMBER: "",
        COMMAND: "switch_on_off",
        STATE: "on",
    }

    DEFAULT_DATA_LED: Dict[str, str] = {SERIAL_NUMBER: "", COMMAND: LED_ON}

    def __init__(
        self,
        username: str,
        password: str,
        headers: Dict[str, str] = HEADERS,
        time_cache: int = CHANGE_TIME_CACHE_DEFAULT,
        access_token: Optional[str] = None,
        token_type: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        """Init method."""
        self.default_headers: Dict[str, str] = headers
        self.access_token: Optional[str] = access_token
        self.token_type: Optional[str] = token_type
        self._latest_status: Dict[str, Any] = {}
        self.session: ClientSession = ClientSession(connector_owner=False)
        self.username: str = username
        self.password: str = password
        self.refresh_token: Optional[str] = refresh_token
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.geofences: Dict[str, Dict[str, Any]] = {}
        self._latest_humidity: Optional[float] = None
        self._latest_temp: Optional[float] = None
        self._time_cache: int = time_cache
        self.fetch_timestamp: Optional[datetime] = None

    def _get_headers(self) -> Dict[str, str]:
        headers = self.default_headers.copy()
        headers.update(
            {"Authorization": "%s %s" % (self.token_type, self.access_token)}
        )
        _LOGGER.debug(headers)
        return headers

    def sanity_check(self, data: Dict[str, Any], device: str) -> bool:
        """Sanity check method."""
        ret = True
        _latest: Optional[Dict[str, Union[str, Number, None]]] = (
            self._latest_status.get(device)
        )
        if _latest is not None:
            _LOGGER.debug(data)
            left = data[self.TEMP]
            right = _latest[self.TEMP]
            if abs(left - right) > CHANGE_THRESHOLD:
                ret = False
        if (
            self._latest_status
            and self._latest_status.get(device)
            and data[self.HUMIDITY] < MIN_HUMIDITY_ALLOWED
        ):
            ret = False
        return ret

    @property
    def have_connection(self) -> bool:
        """Have connection method."""
        return self.access_token is not None

    async def async_connect(self) -> None:
        """Async connect method."""
        url = MELISSA_URL % "auth/login"
        _LOGGER.info(url)
        data = CLIENT_DATA.copy()
        data.update({"username": self.username, "password": self.password})
        _LOGGER.info(data)
        req = await self.session.post(url, data=data, headers=HEADERS)
        if req.status == 200:
            resp = json.loads(await req.text())
            self.access_token = resp["auth"]["access_token"]
            self.refresh_token = resp["auth"]["refresh_token"]
            self.token_type = resp["auth"]["token_type"]
        else:
            raise ApiException(await req.text(), req.status)

    async def async_fetch(self, url: str) -> str:
        """Async fetch method."""
        response = await self.session.get(url)
        ret: str = await response.text()
        return ret

    async def async_fetch_devices(self) -> Dict[str, Dict[str, Any]]:
        """Async fetch devices method."""
        url = MELISSA_URL % "controllers"
        _LOGGER.info(url)
        headers = self._get_headers()
        req = await self.session.get(url, headers=headers)
        if req.status == 200:
            resp = json.loads(await req.text())
            for controller in resp["_embedded"]["controller"]:
                self.devices[controller["serial_number"]] = controller
        _LOGGER.debug(self.devices)
        return self.devices

    async def async_fetch_geofences(self) -> Dict[str, Dict[str, Any]]:
        """Async fetch geofences method."""
        url = MELISSA_URL % "geofences"
        _LOGGER.info(url)
        headers = self._get_headers()
        req = await self.session.get(url, headers=headers)
        if req.status == 200:
            resp = json.loads(await req.text())
            for geofence in resp["_embedded"]["geofence"]:
                self.geofences[geofence["controller_id"]] = geofence
        _LOGGER.info(self.geofences)
        return self.geofences

    async def async_send(
        self,
        device: str,
        device_type: str = "melissa",
        state_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Async send method."""
        data: Dict[str, Any]
        if device_type == "melissa":
            data = self.DEFAULT_DATA_MELISSA.copy()
        elif device_type == "bobbie":
            data = self.DEFAULT_DATA_BOBBIE.copy()
        elif device_type == "led":
            data = self.DEFAULT_DATA_LED.copy()
        else:
            raise UnsupportedDevice(device_type)

        if state_data:
            data.update(state_data)

        data.update({self.SERIAL_NUMBER: device})
        url = MELISSA_URL % "provider/send"
        _LOGGER.info(url)

        if not self.have_connection:
            await self.async_connect()

        headers = self._get_headers()
        headers.update({"Content-Type": "application/json"})

        input_data = json.dumps(data)
        _LOGGER.debug(input_data)
        req = await self.session.post(url, data=input_data, headers=headers)
        if not req.status == 200:
            raise ApiException(await req.text(), req.status)

        return True

    async def async_status(
        self, test: bool = False, cached: bool = False
    ) -> Dict[str, Any]:
        """Async status method."""
        if (
            cached
            and self.fetch_timestamp
            and self._time_cache
            > (datetime.utcnow() - self.fetch_timestamp).total_seconds()
        ):
            return self._latest_status
        url = MELISSA_URL % "provider/fetch"
        _LOGGER.info(url)
        headers = self._get_headers()
        headers.update({"Content-Type": "application/json"})
        ret = {}
        if not self.devices:
            await self.async_fetch_devices()
        for device in self.devices:
            if str(self.devices[device]["type"]) in ("melissa", "bobbie"):
                input_data = json.dumps({"serial_number": device})
                req = await self.session.post(
                    url, data=input_data, headers=headers
                )
                if req.status == 200:
                    data = json.loads(await req.text())
                    ret[device] = data["provider"]
                elif req.status == 401 and not test:
                    await self.async_connect()
                    return await self.async_status()
                else:
                    raise ApiException(await req.text())
        self.fetch_timestamp = datetime.now(UTC)
        self._latest_status = ret
        return ret

    async def async_cur_settings(self, serial_number: str) -> Dict[str, Any]:
        """Async cur settings method."""
        url = MELISSA_URL % "controllers/%s" % serial_number
        _LOGGER.info(url)
        headers = self._get_headers()
        req = await self.session.get(url, headers=headers)
        if req.status == 200:
            data: Dict[str, Any] = json.loads(await req.text())
        else:
            raise ApiException(await req.text(), req.status)
        _LOGGER.debug(data)
        return data
