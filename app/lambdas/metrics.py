from aws_lambda_typing.responses.api_gateway_proxy import APIGatewayProxyResponseV1
from app.dtos.auth import JwtDTO
from app.models.user import User
from app.utils.auth_decorator import requires_auth
from app.errors.web_errors import exception_boundary
from app.service.metrics import MetricsService
import traceback
import boto3
from aws_lambda_typing import events, context

from app.repository.metrics_repo import MetricsRepository

db = boto3.resource('dynamodb')
sqs_client = boto3.client('sqs')

metrics_repo = MetricsRepository(db)
metrics_processing_service = MetricsService(sqs_client, metrics_repo)

def process_metrics(event: events.SQSEvent, ctx: context.Context ):
    try:
        failed_events = metrics_processing_service.process_event(event)

        return {
            "batchItemFailures":[
                {
                    "itemIdentifier":fe
                }
                for fe in failed_events
            ]
        }
    except Exception as e:
        print(e)
        traceback.print_exc()

@exception_boundary
@requires_auth
def get_url_metrics(event: events.APIGatewayProxyEventV1, ctx: context.Context, user: JwtDTO )-> APIGatewayProxyResponseV1:
