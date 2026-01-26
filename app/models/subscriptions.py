from enum import Enum


class Subscription(str, Enum):
    STANDARD = "std"
    PREMIUM = "pro"

    def to_number(self):
        return 1 if self is Subscription.STANDARD else 2

    @staticmethod
    def from_number(number):
        if number == 1:
            return Subscription.STANDARD
        elif number == 2:
            return Subscription.PREMIUM
        else:
            raise ValueError("Invalid Subscription")