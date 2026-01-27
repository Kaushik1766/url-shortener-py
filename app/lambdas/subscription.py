from app.service.subscription_service import SubscriptionService
from app.utils.auth_decorator import requires_auth
from app.utils.timer import log_performance
from app.errors.web_errors import exception_boundary
import json

import boto3
from aws_lambda_typing.responses import APIGatewayProxyResponseV2

from app.dtos.auth import LoginRequestDTO, SignupRequestDTO, JwtDTO
from app.repository.user_repo import UserRepository
from app.service.auth_service import AuthService
from aws_lambda_typing import events, context

db = boto3.resource('dynamodb')
user_repository = UserRepository(db)
subscription_service = SubscriptionService(user_repository)


@exception_boundary
@requires_auth
def upgrade_subscription(event: events.APIGatewayProxyEventV1,ctx: context.Context, user: JwtDTO)->APIGatewayProxyResponseV2:
    updated_jwt = subscription_service.upgrade_subscription(user)

    return APIGatewayProxyResponseV2(
        statusCode=200,
        body=json.dumps({
            "jwt": updated_jwt
        }),
    )