from app.models.subscriptions import Subscription
from app.utils.timer import log_performance
from typing import cast
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef, PutItemInputTypeDef

from app.constants import DYNAMO_DB_TABLE_NAME
from app.errors.web_errors import WebException, ErrorCodes
from app.models.user import User


class UserRepository:
    def __init__(self, db: DynamoDBServiceResource):
        self.db = db
        self.table = db.Table(DYNAMO_DB_TABLE_NAME)

    @log_performance
    def get_user_by_id(self, user_id: str) -> User:
        user_item = self.table.get_item(
            Key={
                "PK":f"USER#{user_id}",
                "SK":"PROFILE"
            }
        ).get('Item')

        if not user_item:
            raise WebException(
                status_code=404,
                message="User not found",
                error_code=ErrorCodes.USER_NOT_FOUND
            )

        return User(**cast(dict, user_item))

    @log_performance
    def get_user_by_email(self, email: str) -> User:
        userid_item = self.table.get_item(
            Key={
                "PK":"LOOKUP",
                "SK":f"EMAIL#{email}"
            }
        ).get('Item')

        if userid_item is None:
            raise WebException(
                status_code=404,
                message="User not found",
                error_code=ErrorCodes.USER_NOT_FOUND
            )

        userid = str(userid_item.get('ID'))

        return self.get_user_by_id(userid)

    @log_performance
    def add_user(self, user: User):
        put_user : TransactWriteItemTypeDef = {
            "Put":PutItemInputTypeDef(
                TableName=DYNAMO_DB_TABLE_NAME,
                Item={
                    "PK":f"USER#{user.id}",
                    "SK":"PROFILE",
                    **user.model_dump(by_alias=True)
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)"
            ),
        }
        put_user_lookup : TransactWriteItemTypeDef = {
            "Put":PutItemInputTypeDef(
                TableName=DYNAMO_DB_TABLE_NAME,
                Item={
                    "PK":"LOOKUP",
                    "SK":f"EMAIL#{user.email}",
                    "ID": user.id,
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)"
            ),
        }

        self.db.meta.client.transact_write_items(
            TransactItems=[put_user, put_user_lookup],
        )

    def set_user_subscription(self, user_id: str, subscription: Subscription):
        self.table.update_item(
            Key={
                "PK":f"USER#{user_id}",
                "SK":"PROFILE"
            },
            UpdateExpression="SET Subscription = :subscription",
            ExpressionAttributeValues={
                ":subscription": subscription.value,
            }
        )