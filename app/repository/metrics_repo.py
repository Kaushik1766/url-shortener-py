from typing import cast
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from app.models.metrics import DailyAccessMetrics
from app.constants import DYNAMO_DB_TABLE_NAME
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
class MetricsRepository:
    def __init__(self, db: DynamoDBServiceResource):
        self.db = db
        self.table = db.Table(DYNAMO_DB_TABLE_NAME)

    def save_metrics(self, metrics: list[DailyAccessMetrics]):
        failed_messages: list[str] = []
        for metric in metrics:
            try:
                self.table.put_item(
                    Item={
                        "PK": f"SHORTURL#{metric.short_url}",
                        "SK": f"DAY#{metric.day}",
                        **metric.model_dump(by_alias=True),
                    },
                    ConditionExpression="attribute_not_exists(PK) and  attribute_not_exists(SK)",
                )
                continue
            except ClientError as e:
                if e.response['Error']['Code'] != "ConditionalCheckFailedException":
                    failed_messages.extend(metric.message_ids)
                    continue

            update_parts: list[str] = []
            expr_names: dict[str, str] = {}
            expr_values: dict[str, int | dict] = {
                ":zero": 0,
            }

            # Total hits
            update_parts.append(
                "TotalHits = if_not_exists(TotalHits, :zero) + :total_hits"
            )
            expr_values[":total_hits"] = metric.total_hits

            # ByCountry
            for i, (country, count) in enumerate(metric.by_country.items()):
                key = f"#c{i}"
                val = f":c{i}"
                update_parts.append(
                    f"ByCountry.{key} = if_not_exists(ByCountry.{key}, :zero) + {val}"
                )
                expr_names[key] = country
                expr_values[val] = count

            # ByDeviceType
            for i, (device, count) in enumerate(metric.by_device_type.items()):
                key = f"#d{i}"
                val = f":d{i}"
                update_parts.append(
                    f"ByDeviceType.{key} = if_not_exists(ByDeviceType.{key}, :zero) + {val}"
                )
                expr_names[key] = device
                expr_values[val] = count

            # ByReferrer
            for i, (ref, count) in enumerate(metric.by_referrer.items()):
                key = f"#r{i}"
                val = f":r{i}"
                update_parts.append(
                    f"ByReferrer.{key} = if_not_exists(ByReferrer.{key}, :zero) + {val}"
                )
                expr_names[key] = ref
                expr_values[val] = count

            self.table.update_item(
                Key={
                    "PK": f"SHORTURL#{metric.short_url}",
                    "SK": f"DAY#{metric.day}",
                },
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )

        return failed_messages

    def get_url_metrics(self, start_day: str, end_day: str, url: str) -> list[DailyAccessMetrics]:
        metrics_query = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"SHORTURL#{url}") & Key("SK").between(f"DAY#{start_day}", f"DAY#{end_day}"),
        ).get("Items", [])

        if len(metrics_query) == 0:
            return []

        return [
            DailyAccessMetrics(
                **cast(dict, metric)
            )
            for metric in metrics_query
        ]