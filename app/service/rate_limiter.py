import datetime
from functools import wraps
from redis import Redis
from aws_lambda_typing import events, context, responses


class RateLimitingService:
    def __init__(self, client: Redis):
        self.redis_client = client

    def check_access(self, url: str, rate: int):
        current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        window_start = current_time - (current_time%60)
        key = f"rl:{url}:{window_start}"
        val = self.redis_client.incr(key)

        if val == 1:
            self.redis_client.expire(key, 60)

        return val<=rate


    def rate_limit(self,rate: int):

        def decorator(handler):
            @wraps(handler)
            def wrapper(*args, **kwargs):
                nonlocal rate
                event: events.APIGatewayProxyEventV2 = kwargs.get("event", args[0])
                url = event['pathParameters'].get('short_url')

                if self.check_access(url, rate):
                    return handler(*args, **kwargs)
                else:
                    return responses.APIGatewayProxyResponseV2(
                        statusCode=429,
                        body="Too many requests",
                    )
            return wrapper
        return decorator
