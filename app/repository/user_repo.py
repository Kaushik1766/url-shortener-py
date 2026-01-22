from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.errors.web_errors import WebException, ErrorCodes
from app.models.user import User


class UserRepository:
    def __init__(self, db: DynamoDBServiceResource):
        self.db = db
        self.table = db.Table("url-shortener-test")

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
        )