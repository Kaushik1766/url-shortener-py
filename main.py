import boto3
import hashids
import redis
from aws_lambda_typing.responses import APIGatewayProxyResponseV2

from app.constants import DYNAMO_DB_TABLE_NAME, HASHID_SALT
from app.errors.web_errors import WebException
from app.models.subscriptions import Subscription
from app.models.user import User
from app.repository.short_url_repo import ShortURLRepository
from app.repository.user_repo import UserRepository
from app.service.url_service import ShortURLService
from app.utils import base62

def main():

    db = boto3.resource('dynamodb')
    repo = ShortURLRepository(db)
    redis_client = redis.Redis(host='localhost', port=6379, db=0,decode_responses=True)
    service = ShortURLService(repo, redis_client)
    #
    print(service.create_short_url("https://google.com/","adfasf", Subscription("std")))
    # try:
    #     print(service.get_original_url("stdYo6eY67"))
    # except WebException as e:
    #     print(e.message)
    # except Exception as e:
    #     print(e)
    # print(hashids.Hashids(salt=HASHID_SALT, min_length=7).decode("Yo6eY67")[0])



if __name__ == "__main__":
    main()
