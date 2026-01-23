from typing import List

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef, PutItemInputTypeDef

from app.constants import DYNAMO_DB_TABLE_NAME
from app.errors.web_errors import WebException, ErrorCodes
from app.models import short_url
from app.models.short_url import ShortUrl


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

    def add_url(self, short_url: ShortUrl):
        put_short_url: TransactWriteItemTypeDef = {
            "Put": PutItemInputTypeDef(
                TableName=DYNAMO_DB_TABLE_NAME,
                Item={
                    "PK": f"SHORTURL#{short_url.short_url}",
                    "SK": f"DETAILS",
                    **short_url.model_dump(by_alias=True)
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)"
            )
        }

        put_owner_mapping: TransactWriteItemTypeDef = {
            "Put": PutItemInputTypeDef(
                TableName=DYNAMO_DB_TABLE_NAME,
                Item={
                    "PK": f"USER#{short_url.owner_id}",
                    "SK": f"SHORTURL#{short_url.short_url}",
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)"
            ),
        }

        self.db.meta.client.transact_write_items(
            TransactItems=[put_short_url, put_owner_mapping],
        )

    def get_counter(self) -> int:
        """
        increments dynamo counter by 1 and returns it
        """
        res = self.table.update_item(
            Key={
                "PK": "SHORTURL",
                "SK": "COUNTER"
            },
            UpdateExpression="SET CurrentCount = CurrentCount + :inc",
            ExpressionAttributeValues={
                ":inc": 1,
            },
            ReturnValues='UPDATED_NEW',
        )

        count = res.get('Attributes').get('CurrentCount')
        return count