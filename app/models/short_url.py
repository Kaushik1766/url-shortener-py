from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ShortUrl(BaseModel):
    id:str = Field(alias="ID")
    url: str = Field(alias="URL")
    short_url: str = Field(alias="ShortURL")
    owner_id: str = Field(alias="OwnerID")
    created_at: int = Field(alias="CreatedAt")

    # @field_validator("created_at", mode='before')
    # @classmethod
    # def int_to_time(cls, data) -> datetime:
    #     if isinstance(data, int):
    #         return datetime.fromtimestamp(data)
    #     elif isinstance(data, datetime):
    #         return data
    #     else:
    #         raise TypeError("Invalid data type for created_at time")
