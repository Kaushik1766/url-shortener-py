import datetime
from typing import cast
from app.models.metrics import AccessMetricsSQSMessage
import json
import os

from aws_lambda_typing import events, context
from functools import wraps

from mypy_boto3_sqs.client import SQSClient

class MetricsService:
    def __init__(self, sqs_client: SQSClient):
        self.sqs_client = sqs_client

    def track_metrics(self,func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            try:
                return func(*args, **kwargs)
            except:
                raise
            finally:
                event = cast(events.APIGatewayProxyEventV2, kwargs.get("event", args[0]))
                referrer = event.get('headers',{}).get('referrer')
                ip = event['requestContext']['http']['sourceIp']
                user_agent = event["headers"].get("user-agent", "default")
                url = event['pathParameters'].get("short_url","")

                try:
                    self.sqs_client.send_message(
                        QueueUrl=os.environ["QUEUE_URL"],
                        MessageBody=json.dumps(
                            AccessMetricsSQSMessage(
                                url=url,
                                referrer=referrer,
                                user_agent=user_agent,
                                ip=ip,
                                timestamp=int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()),
                            )
                        )
                    )
                except Exception as e:
                    print(f"failed to send metrics: {e}")
        return wrapper