#user errors
from pydantic import ValidationError
import json
from typing import Callable
from functools import wraps
from enum import Enum

from aws_lambda_typing.responses import APIGatewayProxyResponseV2
from aws_lambda_typing import events, context


class ErrorCodes(str,Enum):
    #user errors
    EMAIL_ALREADY_EXISTS = 1001
    INVALID_CREDENTIALS = 1002
    USER_NOT_FOUND = 1003
    UNEXPECTED_ERROR = 1004

    #shorturl errors
    SHORTURL_NOT_FOUND = 2001

    #miscellaneous errors
    INTERNAL_SERVER_ERROR = 3001
    VALIDATION_ERROR = 3002

class WebException(Exception):
    def __init__(self, status_code: int, message: str, error_code: ErrorCodes ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code

def exception_boundary(func: Callable[[events.APIGatewayProxyEventV2, context.Context], APIGatewayProxyResponseV2]):
    @wraps(func)
    def wrapper(*args, **kwargs)->APIGatewayProxyResponseV2:
        try:
            return func(*args, **kwargs)
        except WebException as e:
            return APIGatewayProxyResponseV2(
                statusCode= e.status_code,
                body= json.dumps({
                    "message": e.message,
                    "code": e.error_code,
                })
            )
        except ValidationError as v:
            return APIGatewayProxyResponseV2(
                statusCode=422,
                body= json.dumps({
                    "message":[
                        f"error in {err['loc'][0]} - {err['msg']}"
                        for err in v.errors()
                    ],
                    "code": ErrorCodes.VALIDATION_ERROR,
                })
            )
        except:
            return APIGatewayProxyResponseV2(
                statusCode= 500,
                body= json.dumps({
                    "message": "Internal Server Error",
                    "code": ErrorCodes.INTERNAL_SERVER_ERROR,
                })
            )


    return wrapper