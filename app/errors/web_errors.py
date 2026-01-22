#user errors
from enum import Enum

EMAIL_ALREADY_EXISTS = 1001
INVALID_CREDENTIALS = 1002
UNEXPECTED_ERROR = 1003

class ErrorCodes(Enum):
    EMAIL_ALREADY_EXISTS = 1001
    INVALID_CREDENTIALS = 1002
    USER_NOT_FOUND = 1003
    UNEXPECTED_ERROR = 1004

class WebException(Exception):
    def __init__(self, status_code: int, message: str, error_code: ErrorCodes ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
