from pydantic import BaseModel, EmailStr, Field


class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=20)

class SignupRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=20)
    name: str = Field(min_length=2, max_length=50)

class JwtDTO(BaseModel):
    id: str
    email: EmailStr
    name: str
    iat: int
    exp: int