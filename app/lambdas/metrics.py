from app.errors.web_errors import ErrorCodes
from app.errors.web_errors import WebException
import json

from app.repository.short_url_repo import ShortURLRepository
import datetime
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
url_repo = ShortURLRepository(db)

metrics_service = MetricsService(sqs_client, metrics_repo, url_repo)

def process_metrics(event: events.SQSEvent, ctx: context.Context ):
    try:
        failed_events = metrics_service.process_event(event)

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
    queries = event.get('queryStringParameters')

    path_params = event.get('pathParameters')
    if path_params is None:
        raise WebException(
            status_code=404,
            message="Url not found",
            error_code=ErrorCodes.SHORTURL_NOT_FOUND
        )

    url = path_params.get('short_url')
    if url is None:
        raise WebException(
            status_code=404,
            message="Url not found",
            error_code=ErrorCodes.SHORTURL_NOT_FOUND
        )

    start_date = datetime.date.today().strftime("%Y-%m-%d")
    end_date = datetime.date.today().strftime("%Y-%m-%d")

    if queries:
        start_date = queries['startDate']
        end_date = queries['endDate']

    print(user.id)
    metrics = metrics_service.get_metrics_by_url(url=url, user_id=user.id, start_day=start_date, end_day=end_date)

    return APIGatewayProxyResponseV1(
        statusCode=200,
        body=json.dumps(
            [
                metric.model_dump(mode='json')
                for metric in metrics
            ]
        ),
    )