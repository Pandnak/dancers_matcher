from datetime import datetime
from sqlmodel import Field, SQLModel
from pydantic import EmailStr, BaseModel
from pydantic_settings import SettingsConfigDict
from schemas import (Sex, StatusType, RequestStatus, UserType)

class Dancer(SQLModel, table=True):
    __tablename__ = "dancer"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sex: Sex = "MALE"
    age: int | None = Field(default=None, index=True)
    height: float | None = Field(default=None, index=True)
    secret_name: str 
    style: str | None = None
    level: str | None = None
    status: StatusType = "IN_SEARCH"
    # user_id: int = Field(default=None, foreign_key="user.id")


class Request(SQLModel, table=True):
    __tablename__ = "request"

    id: int | None = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="dancer.id")
    receiver_id: int = Field(foreign_key="dancer.id")
    status: RequestStatus = Field(default=RequestStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Pair(SQLModel, table=True):
    __tablename__ = "pair"

    id: int | None = Field(default=None, primary_key=True)
    dancer1_id: int = Field(foreign_key="dancer.id")
    dancer2_id: int = Field(foreign_key="dancer.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PairResponse(SQLModel):
    id: int
    dancer1: Dancer
    dancer2: Dancer
    created_at: datetime

class User(SQLModel, table=True):
    user_id: int = Field(default=None, nullable=False, primary_key=True)
    email: str = Field(nullable=True, unique_items=True)
    password: str | None
    name: str
    user_type: UserType = 'DANCER'
    dancer_id: int | None = Field(default=None, index=True, foreign_key='dancer.id')

    model_config = SettingsConfigDict(
        json_schema_extra = {
            "example": {
                "name": "Иван Иванов",
                "email": "admin@admin.com",
                "password": "admin",
                "user_type": "ADMIN",
                "dancer_id": "None"
            }
        })

class UserCrendentials(BaseModel):
    email: EmailStr
    password: str
    user_type: UserType

    model_config = SettingsConfigDict(
        json_schema_extra = {
            "example": {
                "email": "admin@admin.com",
                "password": "admin",
                "user_type": "ADMIN",
                "dancer_id": "None"
            }
        })
