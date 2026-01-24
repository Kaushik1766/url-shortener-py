from app.service.rate_limiter import RateLimitingService
from app.errors.web_errors import exception_boundary
import json
import os

from app.dtos.auth import JwtDTO
from app.dtos.short_url import CreateShortURLRequest
from aws_lambda_typing.responses import APIGatewayProxyResponseV2

from app.utils.auth_decorator import requires_auth
from app.repository.short_url_repo import ShortURLRepository
import boto3
from redis import Redis
from aws_lambda_typing import events, context

from app.service.url_service import ShortURLService

db = boto3.resource('dynamodb')
url_repo = ShortURLRepository(db)
redis_endpoint = os.environ['REDIS_ENDPOINT']
redis_client = Redis(host=redis_endpoint, port=6379, db=0)
rate_limiter = RateLimitingService(redis_client)
url_service = ShortURLService(url_repo, redis_client)

@exception_boundary
@requires_auth
def create_shorturl_handler(event:events.APIGatewayProxyEventV2, ctx: context.Context, user: JwtDTO)-> APIGatewayProxyResponseV2:
    body = event['body']

    req = CreateShortURLRequest(**json.loads(body))

    shorturl = url_service.create_short_url(req.url, user.id, user.subscription)

    return APIGatewayProxyResponseV2(
        statusCode=201,
        body=json.dumps({
            'shortUrl': shorturl
        })
    )



@exception_boundary
@rate_limiter.rate_limit
def get_url_handler(event:events.APIGatewayProxyEventV2, ctx: context.Context):
    path_params = event['pathParameters']

    short_url = path_params.get('short_url', None)

    url = url_service.get_original_url(short_url)
    print(url)

    return APIGatewayProxyResponseV2(
        statusCode=302,
        headers={'Location': url},
    )

