from typing import List

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.constants import DYNAMO_DB_TABLE_NAME
from app.errors.web_errors import WebException, ErrorCodes


class ShortURLRepository:
    def __init__(self, db: DynamoDBServiceResource):
        self.db = db
        self.table = db.Table(DYNAMO_DB_TABLE_NAME)

    def get_url(self, short_url: str) -> str:
        url_item = self.table.get_item(
            Key={
                "PK": f"SHORTURL#{short_url}",
                "SK": f"DETAILS",
            }
        ).get("Item")

        if url_item is None:
            raise WebException(
                status_code=404,
                message="The short URL does not exist",
                error_code=ErrorCodes.SHORTURL_NOT_FOUND
            )

        return url_item["URL"]

    def get_urls_by_user_id(self, user_id: str) -> List[str]:
        url_items = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"USER#{user_id}")&Key("SK").begins_with("SHORTURL")
        ).get("Items")

        return [
            str(item['SK']).split('#')[-1]
            for item in url_items
        ]