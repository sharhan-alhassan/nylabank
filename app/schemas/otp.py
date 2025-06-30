from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema
from datetime import datetime
from uuid import UUID


class OtpBase(BaseSchema):
    email: str = Field(..., description="Email address for OTP")
    otp_code: str = Field(..., description="OTP code")
    expires_on: datetime = Field(..., description="OTP expiration time")
    is_expired: bool = Field(default=False, description="Whether OTP is expired")


class OtpCreate(OtpBase):
    pass


class OtpUpdate(BaseSchema):
    email: Optional[str] = None
    otp_code: Optional[str] = None
    expires_on: Optional[datetime] = None
    is_expired: Optional[bool] = None


class OtpInDBBase(OtpBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class OtpConfirm(BaseSchema):
    email: str = Field(..., description="Email address for OTP")
    otp_code: str = Field(..., description="OTP code")

class Otp(OtpInDBBase):
    pass


class OtpInDB(OtpInDBBase):
    pass

