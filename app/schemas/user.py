from typing import Optional, List
from pydantic import EmailStr, BaseModel, Field
from app.schemas.base import BaseSchema
from datetime import datetime
from uuid import UUID


class Address(BaseModel):
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State or province")
    zip_code: str = Field(..., description="ZIP or postal code", alias="zipCode")
    country: str = Field(..., description="Country name")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "street": "123 Main Street",
                "city": "New York",
                "state": "NY",
                "zipCode": "10001",
                "country": "United States",
            }
        }


class UserBase(BaseSchema):
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str
    date_of_birth: Optional[datetime] = None
    address: Optional[Address] = None


class UserCreate(UserBase):
    password: str
    confirm_password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class UserResponse(BaseSchema):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str
    is_active: bool
    created_at: datetime


class GenericDetailResponse(BaseModel):
    detail: str


class LoginResponse(BaseModel):
    access_token: str
    # refresh_token: str
    token_type: str


class UserAccountDeletedResponse(BaseModel):
    detail: str


class UserList(BaseSchema):
    total_count: int
    page: int
    per_page: int
    total_pages: int
    data: List[User]


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    email: str
    reset_code: str
    new_password: str
    confirm_password: str
