import datetime
from uuid import uuid4

import hashids
import redis.exceptions
from redis import Redis

from app.constants import HASHID_SALT
from app.models.short_url import ShortUrl
from app.models.subscriptions import Subscription
from app.repository.short_url_repo import ShortURLRepository


class ShortURLService:
    def __init__(self, url_repo: ShortURLRepository, redis_client: Redis):
        self.url_repo = url_repo
        self.redis_client = redis_client

    def create_short_url(self, url: str, user_id: str, subscription: Subscription) -> str:
        shortened_url = ""
        try:
            count = self.redis_client.incrby("shorturl:counter", 2)
            shortened_url = hashids.Hashids(
                salt=HASHID_SALT,
                min_length=7
            ).encode(int(count))
        except redis.exceptions.RedisError:
            print("failed to get count from redis, getting from dynamodb")
            count = self.url_repo.get_counter()
            shortened_url = hashids.Hashids(
                salt=HASHID_SALT,
                min_length=7
            ).encode(int(count))

        short_url = ShortUrl(
            ShortURL= subscription + shortened_url,
            ID=str(uuid4()),
            URL=url,
            CreatedAt=int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()),
            OwnerID=user_id,
        )

        self.url_repo.add_url(short_url)

        return shortened_url

    def get_original_url(self, shortened_url: str) -> str:
        ...