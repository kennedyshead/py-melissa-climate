"""Exxceptions for py-melissa-climate"""

from typing import Optional


class _Exception(Exception):
    def __init__(
        self, _message: str, _status_code: Optional[int] = None
    ) -> None:
        self._message = _message
        self._status_code = _status_code

    @property
    def message(self) -> Optional[str]:
        return self._message

    @property
    def status_code(self) -> Optional[int]:
        return self._status_code


class ApiException(_Exception):
    """Api error occured"""


class UnsupportedDevice(_Exception):
    """Unsupported device"""
