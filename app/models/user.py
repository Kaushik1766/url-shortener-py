from app.models.subscriptions import Subscription
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    id: str = Field(alias="ID")
    email: EmailStr = Field(alias="Email")
    password: str = Field(alias="PasswordHash")
    username: str = Field(alias="Username")
    subscription: Subscription = Field(default=Subscription.STANDARD, alias="Subscription")