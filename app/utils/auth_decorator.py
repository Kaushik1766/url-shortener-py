from app.constants import JWT_ALGORITHM
from app.constants import JWT_SECRET
from typing import cast
from functools import wraps

import jwt
from aws_lambda_typing import events

from app.dtos.auth import JwtDTO
from app.errors.web_errors import WebException, ErrorCodes


def requires_auth(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        event  = cast(events.APIGatewayProxyEventV2,kwargs.get('event', args[0]))

        headers = event.get('headers')
        if headers is None:
            raise WebException(status_code=401, message="Unauthorized", error_code=ErrorCodes.UNAUTHORIZED)

        auth_header = headers.get('Authorization')
        if auth_header is None:
            raise WebException(status_code=401, message="Unauthorized", error_code=ErrorCodes.UNAUTHORIZED)

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                JWT_ALGORITHM
            )

            user = JwtDTO(**payload)

            return func(*args, user, **kwargs)

        except Exception as e:
            print(e)
            raise WebException(
                status_code=401,
                message="Unauthorized",
                error_code=ErrorCodes.UNAUTHORIZED
            )



    return wrapper