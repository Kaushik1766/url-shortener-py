from pydantic import BaseModel

class AccessMetricsSQSMessage(BaseModel):
    url: str
    ip: str
    timestamp: int
    referrer: str | None
    user_agent: str