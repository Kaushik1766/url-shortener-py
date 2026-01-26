import datetime
from app.models.metrics import DailyAccessMetrics
from app.models.metrics import DeviceType
import datetime
from typing import cast
from app.models.metrics import AccessMetricsSQSMessage
import json
import os

from aws_lambda_typing import events, context
from functools import wraps

from mypy_boto3_sqs.client import SQSClient

from app.repository.metrics_repo import MetricsRepository


class MetricsService:
    def __init__(self, sqs_client: SQSClient, repo: MetricsRepository):
        self.sqs_client = sqs_client
        self.repo = repo

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
                referrer = event.get('headers',{}).get('referrer',"none")
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

    def process_event(self, event: events.SQSEvent)-> list[str]:
        records = event.get('Records')

        messages = [
            AccessMetricsSQSMessage(
                message_id=r['messageId'],
                **json.loads(r.get('body',""))
            )
            for r in records
        ]

        daily_metrics:dict[tuple[str,str],DailyAccessMetrics] = {}

        for message in messages:
            url = message.url
            day = datetime.datetime.fromtimestamp(message.timestamp, tz= datetime.timezone.utc).strftime('%Y-%m-%d')

            existing_metric = daily_metrics.get((url, day))

            if existing_metric:
                existing_metric.total_hits += 1
                existing_metric.message_ids.append(message.message_id)
                if message.country in existing_metric.by_country:
                    existing_metric.by_country[message.country] += 1
                else:
                    existing_metric.by_country[message.country] = 1

                if message.device in existing_metric.by_device_type:
                    existing_metric.by_device_type[message.device] += 1
                else:
                    existing_metric.by_device_type[message.device] = 1

                if message.referrer in existing_metric.by_referrer:
                    existing_metric.by_referrer[message.referrer] += 1
                else:
                    existing_metric.by_referrer[message.referrer] = 1
            else:
                daily_metrics[(url,day)]  = DailyAccessMetrics(
                    ShortURL=url,
                    Day=day,
                    ByCountry={
                        message.country: 1
                    },
                    TotalHits=1,
                    ByReferrer={
                        message.referrer: 1
                    },
                    ByDeviceType={
                        message.device: 1
                    },
                    message_ids=[message.message_id]
                )


        daily_metrics_list = list(daily_metrics.values())

        return self.repo.save_metrics(daily_metrics_list)
