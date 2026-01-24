from datetime import timedelta
from datetime import timezone
from datetime import datetime
from app.constants import JWT_ALGORITHM
from app.constants import JWT_SECRET
import jwt

from app.dtos.auth import JwtDTO
from app.repository.user_repo import UserRepository
from app.models.subscriptions import Subscription


class SubscriptionService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def upgrade_subscription(self, user_jwt: JwtDTO):
        self.user_repository.set_user_subscription(user_id=user_jwt.id,subscription=Subscription.PREMIUM )

        updated_jwt = jwt.encode(
            JwtDTO(
                id = user_jwt.id,
                name=user_jwt.name,
                email=user_jwt.email,
                subscription=Subscription.PREMIUM,
                iat=int(datetime.now(tz=timezone.utc).timestamp()),
                exp=int(datetime.now(tz=timezone.utc).timestamp() + timedelta(minutes=30).total_seconds()),
            ).model_dump(),
            JWT_SECRET,
            JWT_ALGORITHM
        )

        return updated_jwt