import datetime
from uuid import uuid4

import hashids
import redis.exceptions
from redis import Redis

from app.constants import HASHID_SALT
from app.models.short_url import ShortUrl
from app.models.subscriptions import Subscription
from app.repository.short_url_repo import ShortURLRepository
from app.service.timer import timer


class ShortURLService:
    def __init__(self, url_repo: ShortURLRepository, redis_client: Redis):
        self.url_repo = url_repo
        self.redis_client = redis_client

    @timer
    def create_short_url(self, url: str, user_id: str, subscription: Subscription) -> str:
        shortened_url = subscription
        count = self.url_repo.get_counter()
        shortened_url += hashids.Hashids(
            salt=HASHID_SALT,
            min_length=7
        ).encode(int(count))

        short_url = ShortUrl(
            ShortURL= shortened_url,
            ID=str(uuid4()),
            URL=url,
            CreatedAt=int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()),
            OwnerID=user_id,
        )

        self.url_repo.add_url(short_url)

        return shortened_url

    @timer
    def get_original_url(self, shortened_url: str) -> str:
        orig_url = self.redis_client.get(f"shorturl:{shortened_url}")
        if not orig_url:
            # print("key not found in redis fetching from db")
            orig_url = self.url_repo.get_url(shortened_url)
            self.redis_client.set(f"shorturl:{shortened_url}", orig_url, ex=600)

        return orig_url
