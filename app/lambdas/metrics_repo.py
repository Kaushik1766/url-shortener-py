from app.models.metrics import DailyAccessMetrics
from app.constants import DYNAMO_DB_TABLE_NAME
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
class MetricsRepository:
    def __init__(self, db: DynamoDBServiceResource):
        self.db = db
        self.table = db.Table(DYNAMO_DB_TABLE_NAME)

    def save_metrics(self, metrics: list[DailyAccessMetrics]):
        for metric in metrics:
            self.table.update_item(
                Key={
                    "PK": f"SHORTURL#{metric.short_url}",
                    "SK": f"DAY#{metric.day}",
                },
                UpdateExpression="""
                    SET
                      TotalHits = if_not_exists(TotalHits, :zero) + :one,
                      TTL = :ttl,
                      ByCountry.#country = if_not_exists(ByCountry.#country, :zero) + :one,
                      ByDeviceType.#device = if_not_exists(ByDeviceType.#device, :zero) + :one,
                      ByReferrer.#ref = if_not_exists(ByReferrer.#ref, :zero) + :one
                """,
                ExpressionAttributeNames={
                    "#country": metric.c
                }
            )
