from app.utils.timer import log_performance
import bcrypt
import jwt

from app.constants import JWT_ALGORITHM, JWT_SECRET
from app.dtos.auth import LoginRequestDTO, JwtDTO, SignupRequestDTO
from app.errors.web_errors import WebException, ErrorCodes
from app.models.subscriptions import Subscription
from app.repository.user_repo import UserRepository
from bcrypt import checkpw
from datetime import datetime, timedelta, timezone
from app.models.user import User
from uuid import uuid4



class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    @log_performance
    def login(self, login_req: LoginRequestDTO):
        user = self.user_repository.get_user_by_email(str(login_req.email))

        if not checkpw(login_req.password.encode('utf-8'), user.password.encode('utf-8')):
            raise WebException(
                status_code=401,
                message="Invalid credentials",
                error_code=ErrorCodes.INVALID_CREDENTIALS
            )

        token = jwt.encode (
            payload=JwtDTO(
                id=user.id,
                email=user.email,
                name=user.username,
                iat=int(datetime.now(tz=timezone.utc).timestamp()),
                exp=int(datetime.now(tz=timezone.utc).timestamp() + timedelta(minutes=30).total_seconds()),
                subscription=Subscription.STANDARD
            ).model_dump(),
            algorithm=JWT_ALGORITHM,
            key=JWT_SECRET
        )

        return token

    @log_performance
    def signup(self, signup_req: SignupRequestDTO):
        password_hash = bcrypt.hashpw(signup_req.password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

        self.user_repository.add_user(
            user= User(
                Username=signup_req.name,
                Email=signup_req.email,
                PasswordHash= password_hash,
                ID=str(uuid4()),
            )
        )