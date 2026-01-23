import boto3
import hashids
import redis

from app.constants import DYNAMO_DB_TABLE_NAME, HASHID_SALT
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

    print(service.create_short_url("https://google.com/","adfasf", Subscription("std")))




if __name__ == "__main__":
    main()
