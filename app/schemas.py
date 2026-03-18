from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class PriorityEnum(str, Enum):
    BUSINESS_CRITICAL = "BUSINESS_CRITICAL"
    MISSION_CRITICAL = "MISSION_CRITICAL"
    BUSINESS_OPERATION = "BUSINESS_OPERATION"
    # Backward compatibility
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"

class TribeBase(BaseModel):
    name: str
    priority: PriorityEnum

class TribeCreate(TribeBase):
    pass

class Tribe(TribeBase):
    id: int
    class Config:
        orm_mode = True

class SquadBase(BaseModel):
    name: str
    priority: PriorityEnum
    tribe_id: int
    platforms: List[str] = []
    status: StatusEnum = StatusEnum.ACTIVE

class SquadCreate(SquadBase):
    pass

class Squad(SquadBase):
    id: int
    class Config:
        orm_mode = True
