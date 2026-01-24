from app.errors.web_errors import ErrorCodes
from app.errors.web_errors import WebException
import datetime
from functools import wraps

import hashids
from redis import Redis
from aws_lambda_typing import events, context, responses

from app.constants import HASHID_SALT, STD_RATE_LIMIT, PRO_RATE_LIMIT
from app.models.subscriptions import Subscription


class RateLimitingService:
    def __init__(self, client: Redis):
        self.redis_client = client

    def check_access(self, short_url: str):
        """
        implements rate limit check and shorturl sanity check
        :param short_url: shortened url
        :return: bool
        """
        if not (short_url.startswith(Subscription.STANDARD.value) or short_url.startswith(Subscription.PREMIUM.value)):
            raise WebException(
                status_code=404,
                message="Invalid short url",
                error_code=ErrorCodes.SHORTURL_NOT_FOUND
            )

        trimmed_short_url = short_url[3:]
        decoded_short_url = hashids.Hashids(salt=HASHID_SALT, min_length=7).decode(trimmed_short_url)
        if len(decoded_short_url) == 0:
            raise WebException(
                status_code=404,
                message="Invalid short url code",
                error_code=ErrorCodes.SHORTURL_NOT_FOUND
            )

        rate = STD_RATE_LIMIT if short_url.startswith(Subscription.STANDARD.value) else PRO_RATE_LIMIT

        current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        window_start = current_time - (current_time%60)
        key = f"rl:{short_url}:{window_start}"
        updated_val = str(self.redis_client.incr(key))

        val = int(updated_val)
        if val == 1:
            self.redis_client.expire(key, 60)

        print(f"val: {val} rate: {rate}")
        return val<=rate


    def rate_limit(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            event: events.APIGatewayProxyEventV2 = kwargs.get("event", args[0])
            url = event['pathParameters'].get('short_url')

            if not url:
                raise WebException(
                    status_code=404,
                    message="Not Found",
                    error_code=ErrorCodes.SHORTURL_NOT_FOUND
                )
            if self.check_access(url):
                return func(*args, **kwargs)
            else:
                raise WebException(
                    status_code=429,
                    message="Too Many Requests, Please try again later",
                    error_code=ErrorCodes.TOO_MANY_REQUESTS
                )
        return wrapper