"""Client for the BrewBrain web application."""

from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urljoin

from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from .const import (
    CLASS_FLOAT_IDENTIFIER,
    CLASS_LATEST_MEASUREMENT,
    CLASS_MEASUREMENT,
    CLASS_MEASUREMENT_NAME,
    URL_BASE,
    URL_FLOAT,
    URL_FLOATS,
    URL_LOGIN,
)

REQUEST_TIMEOUT = 30
LATEST_MEASUREMENTS_PATTERN = re.compile(r"/APIKey/latestMeasurements/\d+")
NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


class BrewBrainError(Exception):
    """Base exception for BrewBrain client errors."""


class BrewBrainAuthenticationError(BrewBrainError):
    """Raised when BrewBrain rejects the credentials."""


class BrewBrainConnectionError(BrewBrainError):
    """Raised when BrewBrain cannot be reached."""


class BrewBrainParseError(BrewBrainError):
    """Raised when the BrewBrain response cannot be parsed."""


@dataclass(frozen=True)
class BrewBrainFloat:
    """A BrewBrain Float registered in an account."""

    identifier: str
    name: str


@dataclass(frozen=True)
class BrewBrainFloatData:
    """Latest measurements for one BrewBrain Float."""

    device: BrewBrainFloat
    measurements: dict[str, float]


class BrewBrainClient:
    """Fetch data from the BrewBrain web application."""

    def __init__(
        self,
        username: str,
        password: str,
    ) -> None:
        """Initialize the client."""
        self._username = username
        self._password = password

    async def async_validate_credentials(self) -> None:
        """Validate credentials and confirm that the account can be read."""
        cookie = await self._async_login()
        await self._async_list_floats(cookie)

    async def async_get_all_data(self) -> dict[str, BrewBrainFloatData]:
        """Fetch every Float and its latest measurements."""
        cookie = await self._async_login()
        devices = await self._async_list_floats(cookie)
        data: dict[str, BrewBrainFloatData] = {}

        for device in devices:
            measurements = await self._async_get_float_measurements(
                cookie, device.identifier
            )
            data[device.identifier] = BrewBrainFloatData(device, measurements)

        return data

    async def _async_login(self) -> str:
        payload = {
            "name": self._username,
            "password": self._password,
            "stay_signed_in": "off",
        }

        try:
            # Keep a dedicated cookie-aware session for the complete login
            # redirect chain. Home Assistant's shared session intentionally
            # uses a dummy cookie jar and breaks BrewBrain authentication.
            async with ClientSession() as session:
                async with session.post(
                    URL_LOGIN,
                    data=payload,
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    if response.status != 200:
                        raise BrewBrainAuthenticationError(
                            "BrewBrain login was not accepted"
                        )
                    cookie_header = response.headers.get("Set-Cookie")
                    if cookie_header is None:
                        raise BrewBrainAuthenticationError(
                            "BrewBrain did not return a session cookie"
                        )
                    return cookie_header.split(";", 1)[0]
        except BrewBrainAuthenticationError:
            raise
        except (ClientError, TimeoutError) as err:
            raise BrewBrainConnectionError("Error requesting BrewBrain login") from err

    async def _async_list_floats(self, cookie: str) -> list[BrewBrainFloat]:
        html = await self._async_post_with_cookie(cookie, URL_FLOATS)
        return _parse_float_list(html)

    async def _async_get_float_measurements(
        self, cookie: str, float_identifier: str
    ) -> dict[str, float]:
        html = await self._async_post_with_cookie(
            cookie, f"{URL_FLOAT}{float_identifier}"
        )
        latest_url = _parse_latest_measurements_url(html)

        html = await self._async_post_with_cookie(cookie, latest_url)
        return _parse_measurements(html)

    async def _async_post_with_cookie(self, cookie: str, url: str) -> str:
        """POST using the session cookie, matching the original integration."""
        try:
            async with ClientSession() as session:
                async with session.post(
                    url,
                    headers={"Cookie": cookie},
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    if response.status in (401, 403):
                        raise BrewBrainAuthenticationError
                    if response.status != 200:
                        raise BrewBrainConnectionError(
                            f"BrewBrain returned HTTP {response.status} for {url}"
                        )
                    return await response.text()
        except (BrewBrainAuthenticationError, BrewBrainConnectionError):
            raise
        except (ClientError, TimeoutError) as err:
            raise BrewBrainConnectionError(f"Error requesting {url}") from err


def _parse_float_list(html: str) -> list[BrewBrainFloat]:
    soup = BeautifulSoup(html, "html.parser")
    devices: list[BrewBrainFloat] = []

    for container in soup.find_all("div", class_=CLASS_FLOAT_IDENTIFIER):
        link = container.find("a", href=True)
        if link is None:
            continue
        identifier = link["href"].rstrip("/").split("/")[-1]
        name = link.get_text(strip=True)
        if identifier and name:
            devices.append(BrewBrainFloat(identifier, name))

    if not devices:
        raise BrewBrainParseError("No BrewBrain Float devices found in the account")
    return devices


def _parse_latest_measurements_url(html: str) -> str:
    match = LATEST_MEASUREMENTS_PATTERN.search(html)
    if match is None:
        raise BrewBrainParseError("Latest measurements URL was not found")
    return urljoin(URL_BASE, match.group(0))


def _parse_measurements(html: str) -> dict[str, float]:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", class_=CLASS_MEASUREMENT)
    if container is None:
        raise BrewBrainParseError("Latest measurements container was not found")

    measurements: dict[str, float] = {}
    for measurement in container.find_all("div", class_=CLASS_LATEST_MEASUREMENT):
        name_element = measurement.find("span", class_=CLASS_MEASUREMENT_NAME)
        value_element = measurement.find("b")
        if name_element is None or value_element is None:
            continue

        match = NUMBER_PATTERN.search(value_element.get_text(strip=True))
        if match is None:
            continue
        measurements[name_element.get_text(strip=True)] = float(
            match.group(0).replace(",", ".")
        )

    if not measurements:
        raise BrewBrainParseError("No BrewBrain measurements could be parsed")
    return measurements
