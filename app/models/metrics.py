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