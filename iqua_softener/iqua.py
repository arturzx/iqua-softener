import logging
from enum import Enum, IntEnum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
try:
    from zoneinfo import ZoneInfo
except:
    from backports.zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)


DEFAULT_API_BASE_URL = "https://apioem.ecowater.com/v1"
DEFAULT_USER_AGENT = "okhttp/4.9.1"


class IquaSoftenerState(str, Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"


class IquaSoftenerVolumeUnit(IntEnum):
    GALLONS = 0
    LITERS = 1


class IquaSoftenerException(Exception):
    pass


@dataclass(frozen=True)
class IquaSoftenerData:
    timestamp: datetime
    model: str
    state: IquaSoftenerState
    device_date_time: datetime
    volume_unit: IquaSoftenerVolumeUnit
    current_water_flow: float
    today_use: int
    average_daily_use: int
    total_water_available: int
    days_since_last_regeneration: int
    salt_level: int
    salt_level_percent: int
    out_of_salt_estimated_days: int
    hardness_grains: int
    water_shutoff_valve_state: int


class IquaSoftener:
    def __init__(
        self,
        username: str,
        password: str,
        device_serial_number: str,
        api_base_url: str = DEFAULT_API_BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self._username: str = username
        self._password: str = password
        self._device_serial_number = device_serial_number
        self._api_base_url: str = api_base_url
        self._user_agent: str = user_agent
        self._token: Optional[str] = None
        self._token_type: Optional[str] = None
        self._token_expiration_timestamp: Optional[datetime] = None

    @property
    def device_serial_number(self) -> str:
        return self._device_serial_number

    def get_data(self) -> IquaSoftenerData:
        with requests.Session() as session:
            self._check_token(session)
            url = self._get_url(f"system/{self._device_serial_number}/dashboard")
            headers = self._get_headers()
            response = session.get(url, headers=headers)
            if response.status_code == 401:
                self._update_token(session)
                response = session.get(url, headers=headers)
            elif response.status_code != 200:
                raise IquaSoftenerException(
                    f"Invalid status ({response.status_code}) for data request"
                )
            if response.status_code != 200:
                raise IquaSoftenerException(
                    f"Invalid status ({response.status_code}) for data request"
                )
            response_data = response.json()
            if response_data.get("code") != "OK":
                raise IquaSoftenerException(
                    f'Invalid response code for data request: {response_data["code"]} ({response_data["message"]})'
                )
            data = response_data["data"]
            return IquaSoftenerData(
                timestamp=datetime.now(),
                model=f'{data["modelDescription"]["value"]} ({data["modelId"]["value"]})',
                state=IquaSoftenerState(data["power"]),
                device_date_time=datetime.fromisoformat(
                    data["deviceDate"][: len(data["deviceDate"]) - 1]
                ).replace(tzinfo=ZoneInfo(data["timeZoneEnum"]["value"])),
                volume_unit=IquaSoftenerVolumeUnit(
                    int(data["volumeUnitEnum"]["value"])
                ),
                current_water_flow=float(data["currentWaterFlow"]["value"]),
                today_use=int(data["gallonsUsedToday"]["value"]),
                average_daily_use=int(data["avgDailyUseGallons"]["value"]),
                total_water_available=int(data["totalWaterAvailGals"]["value"]),
                days_since_last_regeneration=int(data["daysSinceLastRegen"]["value"]),
                salt_level=int(int(data["saltLevelTenths"]["value"]) / 10),
                salt_level_percent=int(data["saltLevelTenths"]["percent"]),
                out_of_salt_estimated_days=int(data["outOfSaltEstDays"]["value"]),
                hardness_grains=int(data["hardnessGrains"]["value"]),
                water_shutoff_valve_state=int(data["waterShutoffValveReq"]["value"])
            )

    def set_water_shutoff_valve(self, state: int):
        if state not in (0, 1):
            raise ValueError("Invalid state for water shut off valve (should be 0 or 1).")
        with requests.Session() as session:
            self._check_token(session)
            url = self._get_url(f"system/{self._device_serial_number}/properties")
            headers = self._get_headers()
            json = {"waterShutoffValve": state}
            response = session.put(url, json=json, headers=headers)
            if response.status_code == 401:
                self._update_token(session)
                response = session.put(url, json=json, headers=headers)
            elif response.status_code != 200:
                raise IquaSoftenerException(
                    f"Invalid status ({response.status_code}) for set water shutoff valve request"
                )
            if response.status_code != 200:
                raise IquaSoftenerException(
                    f"Invalid status ({response.status_code}) for set water shutoff valve request"
                )
            response_data = response.json()
            if response_data.get("code") != "OK":
                raise IquaSoftenerException(
                    f'Invalid response code for set water shutoff valve request: {response_data["code"]} '
                    f'({response_data["message"]})'
                )

    def _check_token(self, session: requests.Session):
        if self._token is None or (
                self._token_expiration_timestamp is not None
                and datetime.now() > self._token_expiration_timestamp
        ):
            self._update_token(session)

    def _update_token(self, session: requests.Session):
        try:
            response = session.post(
                self._get_url("auth/signin"),
                json=dict(username=self._username, password=self._password),
                headers=self._get_headers(with_authorization=False),
            )
        except requests.exceptions.RequestException as ex:
            raise IquaSoftenerException(f"Exception on token request ({ex})")
        if response.status_code == 401:
            raise IquaSoftenerException(f"Authentication error ({response.text})")
        if response.status_code != 200:
            raise IquaSoftenerException(
                f"Invalid status ({response.status_code}) for token request"
            )
        response_data = response.json()
        if response_data.get("code") != "OK":
            raise IquaSoftenerException(
                f'Invalid response code for token request: {response_data["code"]} ({response_data["message"]})'
            )
        self._token = response_data["data"]["token"]
        self._token_type = response_data["data"]["tokenType"]
        self._token_expiration_timestamp = datetime.now() + timedelta(
            seconds=int(response_data["data"]["expiresIn"])
        )

    def _get_url(self, resource: str) -> str:
        return f"{self._api_base_url}/{resource}"

    def _get_headers(self, with_authorization: bool = True) -> Dict[str, str]:
        headers = {"User-Agent": self._user_agent}
        if (
            with_authorization is True
            and self._token is not None
            and self._token_type is not None
        ):
            headers["Authorization"] = f"{self._token_type} {self._token}"
        return headers
