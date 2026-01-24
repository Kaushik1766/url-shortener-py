from pydantic import BaseModel

class CreateShortURLRequest(BaseModel):
    url: str