from enum import Enum
from sqlmodel import SQLModel


class StatusType(str, Enum):
    IN_PAIR = "IN_PAIR"
    IN_SEARCH = "IN_SEARCH"
    
class Sex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class RequestStatus(str, Enum):
    ACCEPTED = "ACCEPTED" 
    PENDING = "PENDING" 
    REJECTED = "REJECTED" 


class UserType(str, Enum):
    ADMIN = "ADMIN" 
    DANCER = "DANCER" 
    

class RequestCreate(SQLModel):
    sender_id: int
    receiver_id: int

class RequestUpdate(SQLModel):
    status: RequestStatus