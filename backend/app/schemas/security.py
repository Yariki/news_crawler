from enum import StrEnum
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.utils.validation import validate_password


class TokenType(StrEnum):
    ACCESS = 'access'
    REFRESH = 'refresh'

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    access_token_exp: float
    refresh_token_exp: float
    token_type: str = "Bearer"

class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)

class LoginRequest(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        validate_password(password)
        return password
    
    
class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)

class MeRequest(BaseModel):
    access_token: str = Field(min_length=1)
