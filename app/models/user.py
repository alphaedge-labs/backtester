from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserSignup(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str
    active_subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserInDB(UserBase):
    id: str
    hashed_password: str
    active_subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
