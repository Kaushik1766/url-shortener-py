import datetime

from app.models.metrics import DailyAccessMetrics
from app.repository.metrics_repo import MetricsRepository
import boto3
import hashids
import redis
from aws_lambda_typing.responses import APIGatewayProxyResponseV2
from pydantic import ValidationError

from app.constants import DYNAMO_DB_TABLE_NAME, HASHID_SALT
from app.errors.web_errors import WebException
from app.models.subscriptions import Subscription
from app.models.user import User
from app.repository.short_url_repo import ShortURLRepository
from app.repository.user_repo import UserRepository
from app.service.url_service import ShortURLService

def main():

    db = boto3.resource('dynamodb')
    repo = MetricsRepository(db)
    # redis_client = redis.Redis(host='localhost', port=6379, db=0,decode_responses=True)
    # service = ShortURLService(repo, redis_client)
    #
    # print(service.create_short_url("https://google.com/","adfasf", Subscription("std")))
    # try:
    #     print(service.get_original_url("stdYo6eY67"))
    # except WebException as e:
    #     print(e.message)
    # except Exception as e:
    #     print(e)
    # print(hashids.Hashids(salt=HASHID_SALT, min_length=7).decode("Yo6eY67")[0])
    print(hashids.Hashids(salt=HASHID_SALT, min_length=8).encode("ds"))
    repo.save_metrics([
        DailyAccessMetrics(
            ByCountry={
                "IN":10,
            },
            ShortURL="stdBZ9Ll98",
            TotalHits=5,
            ByReferrer={
                "twitter.com":10,
            },
            ByDeviceType={
                "desktop": 1
            },
            Day=datetime.date.today().strftime("%Y-%m-%d"),
        ),
        DailyAccessMetrics(
            ByCountry={
                "IN":10,
            },
            ShortURL="stdBZ9Ll98",
            TotalHits=5,
            ByReferrer={
                "twitter.com":10,
            },
            ByDeviceType={
                "desktop": 1
            },
            Day= "2026-01-25"
        )
    ])
    table = db.Table(DYNAMO_DB_TABLE_NAME)

    # item = table.get_item(Key={
    #     "PK":"SHORTURL#stdBZ9Ll98",
    #     "SK":"DAY#2026-01-26"
    # })["Item"]
    # x = DailyAccessMetrics(**item)
    # print(x.by_country["IN"])


if __name__ == "__main__":
    main()
