from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

class PersonType(str, Enum):
    INDIVIDUAL = "individual"

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr

    first_name: str | None = None
    last_name: str | None = None

    phone: str | None = None

    is_active: bool
    is_admin: bool
    created_at: datetime