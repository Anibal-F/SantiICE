from pydantic import BaseModel
from typing import List, Optional

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class User(BaseModel):
    username: str
    role: str
    permissions: List[str]
    is_active: bool = True

class UserInDB(User):
    hashed_password: str