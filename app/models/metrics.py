from decimal import Decimal
from datetime import date
from pydantic import Field
from enum import Enum

from pydantic import BaseModel

class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    SMART_TV = "smart_tv"
    TABLET = "tablet"

class AccessMetricsSQSMessage(BaseModel):
    url: str
    ip: str
    timestamp: int
    referrer: str | None
    user_agent: str
    country: str
    device: DeviceType
    message_id: str = Field(exclude=True, default="")

class DailyAccessMetrics(BaseModel):
    short_url: str = Field(alias="ShortURL")
    day: str = Field(alias="Day")
    total_hits: int = Field(alias="TotalHits")
    by_country: dict = Field(alias="ByCountry")
    by_device_type: dict = Field(alias="ByDeviceType")
    by_referrer: dict = Field(alias="ByReferrer")
    message_ids: list[str] = Field(exclude=True, default=[])

    class Config:
        json_encoders = {
            Decimal: int
        }