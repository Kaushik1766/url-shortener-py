import boto3
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef, PutItemInputTypeDef

from app.constants import DYNAMO_DB_TABLE_NAME
from app.errors.web_errors import WebException, ErrorCodes
from app.models.user import User


class UserRepository:
    def __init__(self, db: DynamoDBServiceResource):
        self.db = db
        self.table = db.Table(DYNAMO_DB_TABLE_NAME)

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

        return User(**user_item)

    def get_user_by_email(self, email: str) -> User:
        userid_query = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"USER#{email}")&Key("SK").begins_with("ID")
        ).get('Items')

        if len(userid_query) == 0:
            raise WebException(
                status_code=404,
                message="User not found",
                error_code=ErrorCodes.USER_NOT_FOUND
            )

        sk : str = userid_query[0]['SK']
        userid = sk.split('#')[1]

        return self.get_user_by_id(userid)

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
                    "PK":f"USER#{user.email}",
                    "SK":f"ID#{user.id}",
                },
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)"
            ),
        }

        self.db.meta.client.transact_write_items(
            TransactItems=[put_user, put_user_lookup],
        )