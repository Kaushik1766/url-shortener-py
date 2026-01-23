import json

import boto3
from aws_lambda_typing.responses import APIGatewayProxyResponseV2

from app.dtos.auth import LoginRequestDTO
from app.repository.user_repo import UserRepository
from app.service.auth_service import AuthService
from aws_lambda_typing import events, context

db = boto3.resource('dynamodb')
user_repository = UserRepository(db)
auth_service = AuthService(user_repository)

def login_handler(event:events.APIGatewayProxyEventV2, ctx: context.Context)->APIGatewayProxyResponseV2:
    body = json.loads(event.get('body'))
    login_req = LoginRequestDTO(**body)

    jwt = auth_service.login(login_req)

    return APIGatewayProxyResponseV2(
        statusCode=200,
        body=json.dumps({
            "jwt": jwt
        }),
    )