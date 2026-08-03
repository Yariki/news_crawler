from enum import StrEnum
from pydantic import BaseModel


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
    refresh_token: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str
    
class LogoutRequest(BaseModel):
    refresh_token: str 

class MeRequest(BaseModel):
    access_token: str
