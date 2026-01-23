from enum import Enum


class Subscription(str, Enum):
    STANDARD = "std"
    PREMIUM = "pro"

