from app.models.metrics import DeviceType
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
                event = cast(events.APIGatewayProxyEventV1, kwargs.get("event", args[0]))

                print(event.get('headers'))
                referrer = event.get('headers',{}).get('referrer')
                ip = event['requestContext']['identity']['sourceIp']
                headers = event.get('headers')
                user_agent = headers.get("User-Agent", "default")
                country = headers.get("CloudFront-Viewer-Country", "unknown")
                device = DeviceType.DESKTOP

                if headers.get("CloudFront-Is-Mobile-Viewer"):
                    device = DeviceType.MOBILE
                elif headers.get("CloudFront-Is-SmartTV-Viewer"):
                    device = DeviceType.SMART_TV
                elif headers.get("CloudFront-Is-Tablet-Viewer"):
                    device = DeviceType.TABLET
                else:
                    device = DeviceType.DESKTOP


                url = cast(dict[str,str],event.get("pathParameters",{})).get("short_url","")

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
                                country=country,
                                device=device,
                            ).model_dump()
                        )
                    )
                except Exception as e:
                    print(f"failed to send metrics: {e}")
        return wrapper